import csv
import random
from datetime import datetime, timedelta

products = [
    {"id": "PROD-101", "name": "Smartphone Galaxy", "base_price": 899.99, "base_demand": 25, "seasonality": "tech", "categoria": "Electrónica", "marca": "Samsung"},
    {"id": "PROD-102", "name": "Zapatillas Running", "base_price": 120.00, "base_demand": 40, "seasonality": "stable", "categoria": "Ropa y Calzado", "marca": "Nike"},
    {"id": "PROD-103", "name": "Chaqueta Invierno", "base_price": 85.50, "base_demand": 10, "seasonality": "winter", "categoria": "Ropa y Calzado", "marca": "NorthFace"},
    {"id": "PROD-104", "name": "Protector Solar FPS50", "base_price": 15.00, "base_demand": 5, "seasonality": "summer", "categoria": "Salud y Belleza", "marca": "Nivea"},
    {"id": "PROD-105", "name": "Cafetera Espresso", "base_price": 250.00, "base_demand": 8, "seasonality": "holiday", "categoria": "Hogar", "marca": "DeLonghi"},
    {"id": "PROD-106", "name": "Silla Gamer", "base_price": 199.90, "base_demand": 15, "seasonality": "stable", "categoria": "Muebles", "marca": "SecretLab"},
]

start_date = datetime(2025, 6, 1)
end_date = datetime(2026, 3, 15)

rows = []
stocks = {p["id"]: random.randint(100, 300) for p in products}

current = start_date
while current <= end_date:
    month = current.month
    
    # Simulate weather
    if month in [12, 1, 2]: clima = "Frío"
    elif month in [6, 7, 8]: clima = "Calor"
    else: clima = "Templado"

    for p in products:
        pid = p["id"]
        base = p["base_demand"]
        
        # Seasonality logic
        factor = 1.0
        if p["seasonality"] == "winter" and month in [11, 12, 1, 2]: factor = 2.5
        elif p["seasonality"] == "summer" and month in [5, 6, 7, 8]: factor = 2.5
        elif p["seasonality"] == "holiday" and month in [11, 12]: factor = 3.0
        elif p["seasonality"] == "tech" and month in [8, 11, 12]: factor = 1.8
        
        # Weekend factor
        if current.weekday() >= 5: factor *= 1.3
            
        demand = max(0, int(base * factor + random.gauss(0, base * 0.2)))
        
        # Promotional discount randomly applied
        descuento = 0
        if random.random() < 0.1: # 10% chance of promotion
            descuento = random.choice([10, 20, 30])
            demand = int(demand * (1 + descuento/100)) # More demand if discount
            
        # Update stock
        stocks[pid] = max(0, stocks[pid] - demand)
        if stocks[pid] < 50 and current.weekday() == 0:
            stocks[pid] += random.randint(100, 200) # Restock on mondays
            
        price = round(p["base_price"] * (1 - descuento/100), 2)
        
        rows.append({
            "fecha": current.strftime("%Y-%m-%d"),
            "producto_id": pid,
            "cantidad_vendida": demand,
            "precio": price,
            "stock_actual": stocks[pid],
            # Extra columns!!!
            "nombre_producto": p["name"],
            "categoria": p["categoria"],
            "marca": p["marca"],
            "descuento_porcentaje": descuento,
            "clima_predominante": clima,
            "costo_envio": round(random.uniform(2.0, 10.0), 2)
        })
        
    current += timedelta(days=1)

with open("c:\\xampp\\htdocs\\PredictStock AI\\sample_data_complex.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "fecha", "producto_id", "cantidad_vendida", "precio", "stock_actual",
        "nombre_producto", "categoria", "marca", "descuento_porcentaje", "clima_predominante", "costo_envio"
    ])
    writer.writeheader()
    writer.writerows(rows)
    print("CSV Generado exitosamente.")
