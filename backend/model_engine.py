"""
model_engine.py - Motor de Machine Learning para predicción de demanda.

Implementa la clase PredictionEngine que maneja el preprocesamiento de datos,
entrenamiento de modelos RandomForestRegressor, y generación de predicciones
de demanda con cálculo de stock crítico.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import warnings
import logging

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Motor de predicción de demanda basado en Random Forest.

    Maneja el ciclo completo de ML: preprocesamiento → entrenamiento → inferencia.
    Entrena un modelo independiente por cada producto para capturar
    patrones de estacionalidad individuales.

    Attributes:
        models: Diccionario de modelos entrenados por producto_id.
        scores: Diccionario de métricas R² por producto_id.
        safety_margin: Factor multiplicador para el stock de seguridad.
    """

    def __init__(self, safety_margin: float = 1.5):
        """
        Inicializa el motor de predicción.

        Args:
            safety_margin: Factor de margen de seguridad para stock crítico.
                          1.5 = 50% extra sobre la demanda predicha.
        """
        self.models: Dict[str, RandomForestRegressor] = {}
        self.scores: Dict[str, float] = {}
        self.safety_margin = safety_margin
        self._product_stats: Dict[str, dict] = {}

    # ──────────────────────────────────────────────
    #  Preprocesamiento de datos
    # ──────────────────────────────────────────────

    @staticmethod
    def preprocess(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrae características temporales de la columna 'fecha' para
        capturar patrones de estacionalidad.

        Features extraídas:
            - mes (1-12)
            - dia_semana (0=lunes, 6=domingo)
            - dia_mes (1-31)
            - es_fin_de_semana (0/1)
            - semana_del_ano (1-52)
            - trimestre (1-4)
            - dia_del_ano (1-365)

        Args:
            df: DataFrame con columna 'fecha' (datetime o string).

        Returns:
            DataFrame con las features temporales añadidas.
        """
        df = df.copy()
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.sort_values("fecha")

        # Extraer características de estacionalidad
        df["mes"] = df["fecha"].dt.month
        df["dia_semana"] = df["fecha"].dt.dayofweek
        df["dia_mes"] = df["fecha"].dt.day
        df["es_fin_de_semana"] = (df["dia_semana"] >= 5).astype(int)
        df["semana_del_ano"] = df["fecha"].dt.isocalendar().week.astype(int)
        df["trimestre"] = df["fecha"].dt.quarter
        df["dia_del_ano"] = df["fecha"].dt.dayofyear

        return df

    # ──────────────────────────────────────────────
    #  Entrenamiento del modelo
    # ──────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Entrena un modelo RandomForestRegressor por cada producto.

        Procesa los datos, segmenta por producto, y entrena modelos
        independientes para capturar patrones de demanda individuales.

        Args:
            df: DataFrame con columnas: fecha, producto_id, cantidad_vendida,
                precio, stock_actual.

        Returns:
            Diccionario {producto_id: r2_score} con las métricas de cada modelo.
        """
        df = self.preprocess(df)
        feature_cols = [
            "mes", "dia_semana", "dia_mes", "es_fin_de_semana",
            "semana_del_ano", "trimestre", "dia_del_ano"
        ]

        results: Dict[str, float] = {}
        products = df["producto_id"].unique()

        for product_id in products:
            product_df = df[df["producto_id"] == product_id].copy()

            if len(product_df) < 10:
                logger.warning(
                    f"Producto {product_id}: datos insuficientes "
                    f"({len(product_df)} registros). Se requieren ≥10."
                )
                continue

            # Guardar estadísticas del producto para referencia
            self._product_stats[product_id] = {
                "precio_promedio": product_df["precio"].mean(),
                "demanda_promedio": product_df["cantidad_vendida"].mean(),
                "stock_ultimo": int(product_df.iloc[-1]["stock_actual"]),
                "ultima_fecha": product_df["fecha"].max(),
            }

            X = product_df[feature_cols]
            y = product_df["cantidad_vendida"]

            # Si hay suficientes datos, hacer split train/test
            if len(product_df) >= 20:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            else:
                X_train, X_test, y_train, y_test = X, X, y, y

            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train)

            # Evaluar el modelo
            y_pred = model.predict(X_test)
            score = max(0, r2_score(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)

            self.models[product_id] = model
            self.scores[product_id] = round(score, 4)
            results[product_id] = round(score, 4)

            logger.info(
                f"Producto {product_id}: R²={score:.4f}, MAE={mae:.2f}"
            )

        return results

    # ──────────────────────────────────────────────
    #  Predicción de demanda
    # ──────────────────────────────────────────────

    def predict(
        self,
        product_id: str,
        days: int = 7,
        start_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Predice la demanda futura para un producto específico.

        Args:
            product_id: Identificador del producto.
            days: Horizonte de predicción en días.
            start_date: Fecha de inicio de la predicción. Si es None,
                       usa la fecha actual.

        Returns:
            Diccionario con predicciones diarias, demanda total,
            stock crítico y estado.

        Raises:
            ValueError: Si no existe un modelo entrenado para el producto.
        """
        if product_id not in self.models:
            raise ValueError(
                f"No existe modelo entrenado para el producto '{product_id}'. "
                f"Productos disponibles: {list(self.models.keys())}"
            )

        model = self.models[product_id]
        base_date = start_date or datetime.now()
        predictions = []

        for i in range(days):
            future_date = base_date + timedelta(days=i + 1)
            features = pd.DataFrame([{
                "mes": future_date.month,
                "dia_semana": future_date.weekday(),
                "dia_mes": future_date.day,
                "es_fin_de_semana": 1 if future_date.weekday() >= 5 else 0,
                "semana_del_ano": future_date.isocalendar()[1],
                "trimestre": (future_date.month - 1) // 3 + 1,
                "dia_del_ano": future_date.timetuple().tm_yday,
            }])

            predicted = float(max(0.0, float(model.predict(features)[0])))
            predictions.append({
                "fecha": future_date.strftime("%Y-%m-%d"),
                "demanda_predicha": float(f"{predicted:.2f}"),
            })

        total_demand = sum(p["demanda_predicha"] for p in predictions)
        stats = self._product_stats.get(product_id, {})
        stock_actual = stats.get("stock_ultimo", 0)
        critical_stock: float = float(self.calculate_critical_stock(float(total_demand)))

        # Determinar estado
        if float(stock_actual) <= critical_stock * 0.5:
            estado = "CRITICO"
        elif stock_actual <= critical_stock:
            estado = "RIESGO"
        else:
            estado = "OK"

        return {
            "producto_id": product_id,
            "dias_prediccion": days,
            "demanda_total_predicha": float(f"{total_demand:.2f}"),
            "stock_actual": stock_actual,
            "stock_critico": float(f"{critical_stock:.2f}"),
            "estado": estado,
            "predicciones_diarias": predictions,
            "confianza": self.scores.get(product_id, 0),
        }

    # ──────────────────────────────────────────────
    #  Cálculo de stock crítico
    # ──────────────────────────────────────────────

    def calculate_critical_stock(
        self, predicted_demand: float, safety_margin: Optional[float] = None
    ) -> float:
        """
        Calcula el nivel de stock crítico basado en la demanda predicha
        y un margen de seguridad configurable.

        Fórmula: Stock Crítico = Demanda Predicha × Margen de Seguridad

        Args:
            predicted_demand: Demanda total predicha para el período.
            safety_margin: Factor multiplicador. Si es None, usa el valor
                          por defecto de la instancia.

        Returns:
            Nivel de stock crítico calculado.
        """
        margin = safety_margin if safety_margin is not None else float(self.safety_margin)
        return float(predicted_demand * margin)

    # ──────────────────────────────────────────────
    #  Detección de Stock Muerto ("Hueso")
    # ──────────────────────────────────────────────

    @staticmethod
    def identify_dead_stock(
        df: pd.DataFrame,
        days: int = 60,
        threshold: int = 5,
    ) -> List[Dict]:
        """
        Identifica productos 'hueso' con baja o nula rotación.

        Un producto se considera 'hueso' si en los últimos N días
        sus ventas totales son menores al umbral especificado.

        Args:
            df: DataFrame con datos de ventas históricos.
            days: Ventana de análisis en días (default: 60).
            threshold: Umbral mínimo de ventas para no ser 'hueso'.

        Returns:
            Lista de diccionarios con productos de baja rotación
            y recomendaciones de acción.
        """
        df = df.copy()
        df["fecha"] = pd.to_datetime(df["fecha"])
        cutoff_date = df["fecha"].max() - timedelta(days=days)
        dead_stock = []

        for product_id in df["producto_id"].unique():
            product_df = df[df["producto_id"] == product_id]
            recent = product_df[product_df["fecha"] >= cutoff_date]

            total_recent_sales = recent["cantidad_vendida"].sum() if len(recent) > 0 else 0
            last_sale_date = product_df[
                product_df["cantidad_vendida"] > 0
            ]["fecha"].max()
            stock = int(product_df.iloc[-1]["stock_actual"])

            if total_recent_sales < threshold:
                days_since = (
                    (df["fecha"].max() - last_sale_date).days
                    if pd.notna(last_sale_date) else days
                )

                # Generar recomendación basada en severidad
                if total_recent_sales == 0:
                    rec = "🔴 Liquidar: Sin ventas en el período. Considerar descuento agresivo o donación."
                elif total_recent_sales < threshold / 2:
                    rec = "🟡 Promocionar: Ventas mínimas. Aplicar descuento del 30-50%."
                else:
                    rec = "🟠 Monitorear: Ventas bajas. Revisar pricing y visibilidad."

                dead_stock.append({
                    "producto_id": product_id,
                    "dias_sin_ventas_significativas": days_since,
                    "ultima_venta": (
                        last_sale_date.strftime("%Y-%m-%d")
                        if pd.notna(last_sale_date) else None
                    ),
                    "ventas_periodo": int(total_recent_sales),
                    "stock_actual": stock,
                    "recomendacion": rec,
                })

        return sorted(dead_stock, key=lambda x: x["ventas_periodo"])

    # ──────────────────────────────────────────────
    #  Comparación ventas reales vs predicción
    # ──────────────────────────────────────────────

    def get_sales_vs_prediction(
        self, df: pd.DataFrame, product_id: str
    ) -> List[Dict]:
        """
        Genera datos comparativos de ventas reales vs predicción del modelo
        para visualización en gráficos.

        Args:
            df: DataFrame con datos históricos de ventas.
            product_id: Producto a analizar.

        Returns:
            Lista de diccionarios con fecha, ventas_reales y prediccion.
        """
        if product_id not in self.models:
            return []

        df = self.preprocess(df)
        product_df = df[df["producto_id"] == product_id].copy()
        feature_cols = [
            "mes", "dia_semana", "dia_mes", "es_fin_de_semana",
            "semana_del_ano", "trimestre", "dia_del_ano"
        ]

        model = self.models[product_id]
        predicted = model.predict(product_df[feature_cols])

        result = []
        for i, (_, row) in enumerate(product_df.iterrows()):
            result.append({
                "fecha": row["fecha"].strftime("%Y-%m-%d"),
                "ventas_reales": float(row["cantidad_vendida"]),
                "prediccion": float(f"{max(0.0, float(predicted[i])):.2f}"),
            })

        return result

    def get_product_stats(self, product_id: str) -> Optional[dict]:
        """Retorna las estadísticas almacenadas de un producto."""
        return self._product_stats.get(product_id)

    @property
    def trained_products(self) -> List[str]:
        """Retorna la lista de productos con modelos entrenados."""
        return list(self.models.keys())
