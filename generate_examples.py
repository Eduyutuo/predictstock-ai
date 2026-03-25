import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_csv(filename, products, base_prices, demand_range, stock_range):
    data = []
    start_date = datetime(2024, 1, 1)
    for i in range(120): # 120 days
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        for prod in products:
            price = base_prices[prod]
            # Seasonality/Randomness
            demand = np.random.randint(demand_range[0], demand_range[1])
            # Add some trend or seasonality to demand
            if "Summer" in prod and i > 120: # Summer peak
                demand += np.random.randint(5, 15)
            
            stock = np.random.randint(stock_range[0], stock_range[1])
            data.append([date, prod, demand, price, stock])
    
    df = pd.DataFrame(data, columns=['fecha', 'producto_id', 'cantidad_vendida', 'precio', 'stock_actual'])
    df.to_csv(filename, index=False)
    print(f"Generated {filename}")

os.makedirs('frontend/public/examples', exist_ok=True)

# Electro
generate_csv('frontend/public/examples/electro_tech_sales.csv', 
            ['Laptop-X1', 'Smartphone-S22', 'Tablet-Pro'],
            {'Laptop-X1': 1200, 'Smartphone-S22': 800, 'Tablet-Pro': 500},
            (1, 5), (10, 50))

# Fashion
generate_csv('frontend/public/examples/fashion_trend_sales.csv', 
            ['T-Shirt-Summer', 'Jeans-Classic', 'Sneakers-V1'],
            {'T-Shirt-Summer': 25, 'Jeans-Classic': 55, 'Sneakers-V1': 90},
            (10, 30), (50, 200))

# Grocery
generate_csv('frontend/public/examples/grocery_market_sales.csv', 
            ['Milk-1L', 'Bread-White', 'Egg-Carton'],
            {'Milk-1L': 1.5, 'Bread-White': 2.0, 'Egg-Carton': 3.5},
            (50, 150), (200, 1000))
