"""
models.py - Esquemas Pydantic para validación de datos.

Define los modelos de request/response para la API con tipado estricto
y validación automática.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


# ──────────────────────────────────────────────
#  Esquemas de entrada (Request)
# ──────────────────────────────────────────────

class SalesRecordSchema(BaseModel):
    """Esquema para un registro individual de ventas."""

    fecha: date = Field(..., description="Fecha de la venta (YYYY-MM-DD)")
    producto_id: str = Field(
        ..., min_length=1, max_length=50,
        description="Identificador único del producto"
    )
    cantidad_vendida: int = Field(
        ..., ge=0,
        description="Cantidad de unidades vendidas"
    )
    precio: float = Field(
        ..., gt=0,
        description="Precio unitario del producto"
    )
    stock_actual: int = Field(
        ..., ge=0,
        description="Stock disponible al momento del registro"
    )

    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    """Parámetros para solicitar una predicción de demanda."""

    producto_id: str = Field(..., description="ID del producto a predecir")
    dias: int = Field(
        default=7, ge=1, le=90,
        description="Horizonte de predicción en días (1-90)"
    )


# ──────────────────────────────────────────────
#  Esquemas de salida (Response)
# ──────────────────────────────────────────────

class DailyPrediction(BaseModel):
    """Predicción de demanda para un día específico."""

    fecha: str
    demanda_predicha: float


class PredictionResponse(BaseModel):
    """Respuesta del endpoint de predicción."""

    producto_id: str
    dias_prediccion: int
    demanda_total_predicha: float
    stock_actual: int
    stock_critico: float
    estado: str  # "OK", "RIESGO", "CRITICO"
    predicciones_diarias: List[DailyPrediction]
    confianza: float = Field(
        ..., ge=0, le=1,
        description="Score de confianza del modelo (R²)"
    )


class InventoryItem(BaseModel):
    """Estado de inventario de un producto individual."""

    producto_id: str
    stock_actual: int
    demanda_predicha_7d: float
    demanda_predicha_30d: float
    stock_critico: float
    precio_promedio: float
    ventas_ultimos_30d: int
    alerta: str  # "VERDE", "AMARILLO", "ROJO"
    mensaje_alerta: str


class InventoryResponse(BaseModel):
    """Respuesta del endpoint de inventario."""

    total_productos: int
    productos_riesgo: int
    productos_baja_rotacion: int
    productos_saludables: int
    inventario: List[InventoryItem]


class DeadStockProduct(BaseModel):
    """Producto identificado como 'hueso' (baja rotación)."""

    producto_id: str
    dias_sin_ventas_significativas: int
    ultima_venta: Optional[str]
    stock_actual: int
    recomendacion: str


class KPIData(BaseModel):
    """Indicadores clave de rendimiento."""

    ventas_proyectadas_30d: float
    ingresos_proyectados_30d: float
    productos_en_riesgo: int
    productos_baja_rotacion: int
    total_productos: int
    stock_total: int


class SalesVsPrediction(BaseModel):
    """Datos para el gráfico comparativo ventas reales vs predicción."""

    fecha: str
    ventas_reales: float
    prediccion: float


class AnalyticsResponse(BaseModel):
    """Respuesta del endpoint de analytics."""

    kpis: KPIData
    productos_hueso: List[DeadStockProduct]
    top_productos: List[dict]
    comparacion_ventas_prediccion: List[SalesVsPrediction]


class UploadResponse(BaseModel):
    """Respuesta del endpoint de carga de datos."""

    mensaje: str
    registros_cargados: int
    productos_unicos: int
    rango_fechas: dict
