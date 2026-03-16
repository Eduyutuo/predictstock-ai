"""
main.py - Aplicación FastAPI para PredictStock AI.

Configura la API REST con endpoints para carga de datos,
predicción de demanda, gestión de inventario y análisis de rotación.
Todas las rutas son asíncronas (async/await).
"""

import io
import logging
from datetime import datetime
from typing import Optional

import os
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from database import SalesRecord, SessionLocal, init_db
from model_engine import PredictionEngine
from models import (
    AnalyticsResponse,
    InventoryItem,
    InventoryResponse,
    PredictionResponse,
    UploadResponse,
)

# ──────────────────────────────────────────────
#  Configuración de la aplicación
# ──────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PredictStock AI",
    description="Sistema Inteligente de Gestión de Inventarios y Análisis Predictivo",
    version="1.0.0",
)

# CORS para comunicación con el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Motor de predicción global
engine = PredictionEngine(safety_margin=1.5)


@app.on_event("startup")
async def startup():
    """Inicializa la base de datos y entrena el modelo si hay datos existentes."""
    init_db()
    logger.info("✅ Base de datos inicializada")

    # Intentar entrenar con datos existentes en la BD
    df = _load_sales_from_db()
    if df is not None and len(df) > 0:
        engine.train(df)
        logger.info(f"✅ Modelo entrenado con {len(df)} registros existentes")


# ──────────────────────────────────────────────
#  Funciones auxiliares
# ──────────────────────────────────────────────


def _load_sales_from_db() -> Optional[pd.DataFrame]:
    """Carga todos los registros de ventas de la BD como DataFrame."""
    db = SessionLocal()
    try:
        records = db.query(SalesRecord).all()
        if not records:
            return None
        data = [
            {
                "fecha": r.fecha,
                "producto_id": r.producto_id,
                "cantidad_vendida": r.cantidad_vendida,
                "precio": r.precio,
                "stock_actual": r.stock_actual,
            }
            for r in records
        ]
        return pd.DataFrame(data)
    finally:
        db.close()


# ──────────────────────────────────────────────
#  Endpoint: Carga de datos (CSV/JSON)
# ──────────────────────────────────────────────


@app.post("/api/upload", response_model=UploadResponse)
async def upload_sales_data(file: UploadFile = File(...)):
    """
    Recibe un archivo CSV o JSON con historial de ventas y lo almacena en la BD.

    Columnas requeridas:
    - fecha (YYYY-MM-DD)
    - producto_id
    - cantidad_vendida
    - precio
    - stock_actual

    Entrena automáticamente el modelo de predicción tras la carga.
    """
    try:
        content = await file.read()

        # Detectar formato del archivo
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=400,
                detail="Formato no soportado. Use CSV o JSON.",
            )

        # Validar columnas requeridas
        required_cols = {
            "fecha", "producto_id", "cantidad_vendida", "precio", "stock_actual"
        }
        missing = required_cols - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Columnas faltantes: {missing}. "
                       f"Requeridas: {required_cols}",
            )

        # Limpiar y validar datos
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        df["cantidad_vendida"] = pd.to_numeric(
            df["cantidad_vendida"], errors="coerce"
        ).fillna(0).astype(int)
        df["precio"] = pd.to_numeric(df["precio"], errors="coerce").fillna(0)
        df["stock_actual"] = pd.to_numeric(
            df["stock_actual"], errors="coerce"
        ).fillna(0).astype(int)

        # Guardar en la base de datos
        db = SessionLocal()
        try:
            # Limpiar registros anteriores para evitar duplicados
            db.query(SalesRecord).delete()

            for _, row in df.iterrows():
                record = SalesRecord(
                    fecha=row["fecha"],
                    producto_id=str(row["producto_id"]),
                    cantidad_vendida=int(row["cantidad_vendida"]),
                    precio=float(row["precio"]),
                    stock_actual=int(row["stock_actual"]),
                )
                db.add(record)
            db.commit()
        finally:
            db.close()

        # Entrenar el modelo con los nuevos datos
        df["fecha"] = pd.to_datetime(df["fecha"])
        training_scores = engine.train(df)
        logger.info(f"Modelo entrenado. Scores: {training_scores}")

        return UploadResponse(
            mensaje=f"✅ Datos cargados y modelo entrenado exitosamente",
            registros_cargados=len(df),
            productos_unicos=df["producto_id"].nunique(),
            rango_fechas={
                "inicio": str(df["fecha"].min().date()),
                "fin": str(df["fecha"].max().date()),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al procesar archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


# ──────────────────────────────────────────────
#  Endpoint: Predicción de demanda
# ──────────────────────────────────────────────


@app.get("/api/predict/{producto_id}", response_model=PredictionResponse)
async def predict_demand(
    producto_id: str,
    dias: int = Query(default=7, ge=1, le=90, description="Horizonte de predicción"),
):
    """
    Predice la demanda futura para un producto específico.

    Retorna predicciones diarias, demanda total, stock crítico
    y un indicador de estado (OK / RIESGO / CRITICO).
    """
    if not engine.trained_products:
        raise HTTPException(
            status_code=400,
            detail="No hay modelos entrenados. Primero cargue datos vía /api/upload.",
        )

    try:
        result = engine.predict(producto_id, days=dias)
        return PredictionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")


# ──────────────────────────────────────────────
#  Endpoint: Inventario con alertas
# ──────────────────────────────────────────────


@app.get("/api/inventory", response_model=InventoryResponse)
async def get_inventory():
    """
    Retorna el estado del inventario completo con alertas visuales.

    Alertas:
    - 🔴 ROJO: Stock por debajo del nivel crítico (riesgo de quiebre).
    - 🟡 AMARILLO: Producto con baja rotación.
    - 🟢 VERDE: Stock saludable.
    """
    df = _load_sales_from_db()
    if df is None:
        raise HTTPException(
            status_code=400,
            detail="No hay datos cargados. Use /api/upload primero.",
        )

    df["fecha"] = pd.to_datetime(df["fecha"])
    dead_stock_ids = {
        item["producto_id"]
        for item in engine.identify_dead_stock(df)
    }

    inventory = []
    risk_count = 0
    low_rotation = 0
    healthy = 0

    for product_id in df["producto_id"].unique():
        product_df = df[df["producto_id"] == product_id]
        stock = int(product_df.iloc[-1]["stock_actual"])
        avg_price = float(f"{product_df['precio'].mean():.2f}")

        # Ventas últimos 30 días
        cutoff_30d = df["fecha"].max() - pd.Timedelta(days=30)
        recent_sales = int(
            product_df[product_df["fecha"] >= cutoff_30d]["cantidad_vendida"].sum()
        )

        # Predicciones
        try:
            pred_7d = engine.predict(product_id, days=7)
            pred_30d = engine.predict(product_id, days=30)
            demand_7d = pred_7d["demanda_total_predicha"]
            demand_30d = pred_30d["demanda_total_predicha"]
            critical = pred_7d["stock_critico"]
        except (ValueError, Exception):
            demand_7d = 0
            demand_30d = 0
            critical = 0

        # Determinar alerta
        if float(stock) <= float(critical) * 0.5:
            alerta = "ROJO"
            mensaje = f"⚠️ Stock crítico: {stock} unidades. Se necesitan ≥{int(critical)} para cubrir demanda."
            risk_count += 1
        elif product_id in dead_stock_ids:
            alerta = "AMARILLO"
            mensaje = "📦 Baja rotación: sin ventas significativas en 60 días."
            low_rotation += 1
        elif float(stock) <= float(critical):
            alerta = "ROJO"
            mensaje = f"⚠️ Stock en riesgo: {stock} unidades vs {int(critical)} requeridas."
            risk_count += 1
        else:
            alerta = "VERDE"
            mensaje = "✅ Stock saludable."
            healthy += 1

        inventory.append(InventoryItem(
            producto_id=product_id,
            stock_actual=stock,
            demanda_predicha_7d=float(f"{demand_7d:.2f}"),
            demanda_predicha_30d=float(f"{demand_30d:.2f}"),
            stock_critico=float(f"{critical:.2f}"),
            precio_promedio=avg_price,
            ventas_ultimos_30d=recent_sales,
            alerta=alerta,
            mensaje_alerta=mensaje,
        ))

    # Ordenar: ROJO primero, luego AMARILLO, luego VERDE
    order = {"ROJO": 0, "AMARILLO": 1, "VERDE": 2}
    inventory.sort(key=lambda x: order.get(x.alerta, 3))

    return InventoryResponse(
        total_productos=len(inventory),
        productos_riesgo=risk_count,
        productos_baja_rotacion=low_rotation,
        productos_saludables=healthy,
        inventario=inventory,
    )


# ──────────────────────────────────────────────
#  Endpoint: Analytics (KPIs + rotación)
# ──────────────────────────────────────────────


@app.get("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    producto_id: Optional[str] = Query(
        default=None, description="Producto para gráfico comparativo"
    ),
):
    """
    Retorna análisis completo: KPIs, productos 'hueso', top sellers,
    y datos comparativos de ventas reales vs predicción de IA.
    """
    df = _load_sales_from_db()
    if df is None:
        raise HTTPException(
            status_code=400,
            detail="No hay datos cargados. Use /api/upload primero.",
        )

    df["fecha"] = pd.to_datetime(df["fecha"])

    # ── KPIs ──
    total_products = df["producto_id"].nunique()
    total_stock = int(
        df.groupby("producto_id").last()["stock_actual"].sum()
    )

    projected_sales = 0
    projected_revenue = 0
    risk_count = 0

    for pid in engine.trained_products:
        try:
            pred = engine.predict(pid, days=30)
            stats = engine._product_stats.get(pid, {})
            projected_sales = float(projected_sales) + float(pred["demanda_total_predicha"])
            projected_revenue = float(projected_revenue) + float(
                pred["demanda_total_predicha"] * stats.get("precio_promedio", 0)
            )
            if pred["estado"] in ("RIESGO", "CRITICO"):
                risk_count += 1
        except Exception:
            pass

    dead_stock_list = engine.identify_dead_stock(df)

    kpis = {
        "ventas_proyectadas_30d": float(f"{projected_sales:.2f}"),
        "ingresos_proyectados_30d": float(f"{projected_revenue:.2f}"),
        "productos_en_riesgo": risk_count,
        "productos_baja_rotacion": len(dead_stock_list),
        "total_productos": total_products,
        "stock_total": total_stock,
    }

    # ── Top productos ──
    top_products = (
        df.groupby("producto_id")["cantidad_vendida"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
        .to_dict("records")
    )

    # ── Comparación ventas vs predicción ──
    comparison = []
    if producto_id and producto_id in engine.trained_products:
        comparison = engine.get_sales_vs_prediction(df, producto_id)
    elif engine.trained_products:
        # Por defecto, usar el producto más vendido
        default_pid = top_products[0]["producto_id"] if top_products else None
        if default_pid and default_pid in engine.trained_products:
            comparison = engine.get_sales_vs_prediction(df, default_pid)

    return AnalyticsResponse(
        kpis=kpis,
        productos_hueso=dead_stock_list,
        top_productos=top_products,
        comparacion_ventas_prediccion=comparison,
    )


# ──────────────────────────────────────────────
#  Endpoint: Datos de ventas crudos
# ──────────────────────────────────────────────


@app.get("/api/sales")
async def get_sales():
    """Retorna los datos de ventas cargados en formato JSON."""
    df = _load_sales_from_db()
    if df is None:
        return {"data": [], "total": 0}

    df["fecha"] = df["fecha"].astype(str)
    return {
        "data": df.to_dict("records"),
        "total": len(df),
    }


@app.get("/api/products")
async def get_products():
    """Retorna la lista de productos disponibles."""
    df = _load_sales_from_db()
    if df is None:
        return {"products": []}

    products = sorted(df["producto_id"].unique().tolist())
    return {
        "products": products,
        "trained": engine.trained_products,
    }


# ──────────────────────────────────────────────
#  Health Check
# ──────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    """Endpoint de verificación del estado del servicio."""
    return {
        "status": "online",
        "modelo_entrenado": len(engine.models) > 0,
        "productos_entrenados": len(engine.models),
        "version": "1.0.0",
    }


# ──────────────────────────────────────────────
#  Servir el Frontend de React (Para Producción)
# ──────────────────────────────────────────────

# Ruta a la carpeta 'dist' del frontend compilado
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(frontend_dist):
    # Montar los assets estáticos (CSS, JS, imágenes)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Servir index.html para todas las demás rutas (React Router / SPA)
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        # Excluir rutas de API
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
            
        file_path = os.path.join(frontend_dist, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    logger.warning(
        f"Frontend build no encontrado en {frontend_dist}. "
        "Ejecuta 'npm run build' en la carpeta frontend."
    )
