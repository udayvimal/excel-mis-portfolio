import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
import os

# Set up constants
PAYMENT_METHODS = ['UPI', 'Card', 'Cash on Delivery']
CITIES = ['Mumbai', 'Delhi', 'Pune', 'Bangalore', 'Ahmedabad']
NUM_ORDERS = 1000

def random_order_datetime():
    """Generate a random order datetime in last 12 months"""
    start_date = datetime.now() - timedelta(days=365)
    random_date = start_date + timedelta(days=random.randint(0, 365),
                                         seconds=random.randint(0, 86400))
    return random_date.date(), random_date.time().replace(microsecond=0)

def generate_order_data(products_df, num_orders=1000):
    orders = []
    for _ in range(num_orders):
        product = products_df.sample(1).iloc[0]

        order_id = str(uuid.uuid4())
        order_date, order_time = random_order_datetime()

        city = product['city']
        store_id = product['store_id']
        product_category = product['product_category']
        order_value = float(product['price'])
        delivery_time_min = product['delivery_time_min']
        platform = product['platform']
        payment_method = random.choice(PAYMENT_METHODS)

        discount_pct = random.uniform(5, 20)  # 5%–20%
        discount_amount = round(order_value * discount_pct / 100, 2)
        net_order_value = round(order_value - discount_amount, 2)

        orders.append({
            "order_id": order_id,
            "order_date": order_date,
            "order_time": order_time,
            "city": city,
            "store_id": store_id,
            "product_category": product_category,
            "order_value": round(order_value, 2),
            "discount_amount": discount_amount,
            "net_order_value": net_order_value,
            "delivery_time_min": delivery_time_min,
            "payment_method": payment_method,
            "platform": platform
        })

    return pd.DataFrame(orders)

def main():
    if not os.path.exists("data/zepto_products.csv") or not os.path.exists("data/blinkit_products.csv"):
        print("Error: Please ensure 'data/zepto_products.csv' and 'data/blinkit_products.csv' exist.")
        return

    zepto_df = pd.read_csv("data/zepto_products.csv")
    blinkit_df = pd.read_csv("data/blinkit_products.csv")

    combined_df = pd.concat([zepto_df, blinkit_df], ignore_index=True)

    print("✅ Loaded product data. Generating order-level data...")
    order_df = generate_order_data(combined_df, NUM_ORDERS)
    order_df.to_csv("data/generated_order_data.csv", index=False)
    print("✅ Order data saved to 'data/generated_order_data.csv'.")

if __name__ == "__main__":
    main()
