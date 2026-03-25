import random
from datetime import datetime, timedelta
import os

def generate_csv_text(products, prices, demand_range, stock_range, days=120):
    lines = ["fecha,producto_id,cantidad_vendida,precio,stock_actual"]
    start_date = datetime(2024, 1, 1)
    for i in range(days):
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        for prod in products:
            price = prices[prod]
            demand = random.randint(demand_range[0], demand_range[1])
            stock = random.randint(stock_range[0], stock_range[1])
            lines.append(f"{date},{prod},{demand},{price},{stock}")
    return "\n".join(lines)

os.makedirs('frontend/public/examples', exist_ok=True)

# Electro
with open('frontend/public/examples/electro_tech_sales.csv', 'w') as f:
    f.write(generate_csv_text(['Laptop-X1', 'Smartphone-S22', 'Tablet-Pro'],
                             {'Laptop-X1': 1200, 'Smartphone-S22': 800, 'Tablet-Pro': 500},
                             (1, 5), (5, 30)))

# Fashion
with open('frontend/public/examples/fashion_trend_sales.csv', 'w') as f:
    f.write(generate_csv_text(['T-Shirt-Summer', 'Jeans-Classic', 'Sneakers-V1'],
                             {'T-Shirt-Summer': 25, 'Jeans-Classic': 55, 'Sneakers-V1': 90},
                             (10, 40), (20, 150)))

# Grocery
with open('frontend/public/examples/grocery_market_sales.csv', 'w') as f:
    f.write(generate_csv_text(['Milk-1L', 'Bread-White', 'Egg-Carton'],
                             {'Milk-1L': 1.5, 'Bread-White': 2.0, 'Egg-Carton': 3.5},
                             (50, 150), (100, 800)))

print("Success: Generated 3 CSV files with >100 rows each.")
