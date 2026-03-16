"""
generate_sample_data.py - Genera datos de prueba realistas para PredictStock AI.

Crea un CSV con ~500+ registros de ventas para 10 productos
simulando patrones de estacionalidad y tendencia.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

PRODUCTS = [
    {"id": "PROD-001", "name": "Laptop Pro 15", "base_price": 1299.99, "base_demand": 5, "seasonality": "tech"},
    {"id": "PROD-002", "name": "Mouse Ergonómico", "base_price": 49.99, "base_demand": 15, "seasonality": "stable"},
    {"id": "PROD-003", "name": "Teclado Mecánico RGB", "base_price": 129.99, "base_demand": 10, "seasonality": "tech"},
    {"id": "PROD-004", "name": "Monitor 4K 27\"", "base_price": 449.99, "base_demand": 4, "seasonality": "tech"},
    {"id": "PROD-005", "name": "Webcam HD", "base_price": 79.99, "base_demand": 8, "seasonality": "stable"},
    {"id": "PROD-006", "name": "Hub USB-C", "base_price": 39.99, "base_demand": 12, "seasonality": "stable"},
    {"id": "PROD-007", "name": "Auriculares BT Pro", "base_price": 199.99, "base_demand": 7, "seasonality": "holiday"},
    {"id": "PROD-008", "name": "Cable HDMI 2.1", "base_price": 19.99, "base_demand": 20, "seasonality": "stable"},
    {"id": "PROD-009", "name": "Funda Laptop Cuero", "base_price": 59.99, "base_demand": 1, "seasonality": "dead"},  # Producto "hueso"
    {"id": "PROD-010", "name": "Adaptador VGA", "base_price": 14.99, "base_demand": 0, "seasonality": "dead"},  # Producto "hueso"
]

START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2026, 3, 15)


def get_seasonal_factor(date: datetime, seasonality: str) -> float:
    """Calcula factor estacional basado en tipo de producto y fecha."""
    month = date.month
    day_of_week = date.weekday()

    # Factor fin de semana
    weekend_factor = 1.3 if day_of_week >= 5 else 1.0

    if seasonality == "tech":
        # Picos en vuelta a clases (enero, agosto) y Black Friday (noviembre)
        month_factors = {1: 1.4, 2: 1.1, 3: 0.9, 4: 0.8, 5: 0.7,
                        6: 0.8, 7: 0.9, 8: 1.3, 9: 1.2, 10: 1.0,
                        11: 1.6, 12: 1.5}
    elif seasonality == "holiday":
        # Pico en temporada navideña
        month_factors = {1: 0.7, 2: 0.8, 3: 0.8, 4: 0.9, 5: 0.9,
                        6: 1.0, 7: 1.0, 8: 0.9, 9: 1.0, 10: 1.1,
                        11: 1.5, 12: 2.0}
    elif seasonality == "dead":
        # Casi sin ventas
        month_factors = {m: 0.1 for m in range(1, 13)}
    else:  # stable
        month_factors = {m: 1.0 for m in range(1, 13)}

    return month_factors.get(month, 1.0) * weekend_factor


def generate_data():
    """Genera el dataset completo."""
    rows = []
    stocks = {p["id"]: random.randint(50, 200) for p in PRODUCTS}

    current = START_DATE
    while current <= END_DATE:
        for product in PRODUCTS:
            pid = product["id"]
            base = product["base_demand"]
            factor = get_seasonal_factor(current, product["seasonality"])

            # Calcular ventas con ruido aleatorio
            demand = max(0, int(base * factor + random.gauss(0, base * 0.3)))

            # Ajustar stock
            stocks[pid] = max(0, stocks[pid] - demand)

            # Restock semanal (los lunes)
            if current.weekday() == 0 and stocks[pid] < 30:
                stocks[pid] += random.randint(30, 80)

            # Variación de precio (±5%)
            price = round(product["base_price"] * random.uniform(0.95, 1.05), 2)

            rows.append({
                "fecha": current.strftime("%Y-%m-%d"),
                "producto_id": pid,
                "cantidad_vendida": demand,
                "precio": price,
                "stock_actual": stocks[pid],
            })

        current += timedelta(days=1)

    return rows


if __name__ == "__main__":
    data = generate_data()

    with open("sample_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "fecha", "producto_id", "cantidad_vendida", "precio", "stock_actual"
        ])
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Generados {len(data)} registros en sample_data.csv")
    print(f"   Productos: {len(PRODUCTS)}")
    print(f"   Rango: {data[0]['fecha']} → {data[-1]['fecha']}")
