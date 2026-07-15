import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N = 15000
FRAUD_RATE = 0.032   # 3.2%

cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune',
          'Kolkata', 'Ahmedabad', 'Jaipur', 'Lucknow']
upi_apps = ['GPay', 'PhonePe', 'Paytm', 'BHIM', 'Amazon Pay']
app_weights = [0.35, 0.30, 0.20, 0.08, 0.07]
transaction_types = ['P2P', 'P2M', 'Bill Payment', 'Recharge', 'Shopping']
device_types = ['Android', 'iOS', 'Feature Phone']

start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)
date_range = (end_date - start_date).days
timestamps = sorted([start_date + timedelta(
    days=random.randint(0, date_range),
    hours=random.randint(0, 23),
    minutes=random.randint(0, 59),
    seconds=random.randint(0, 59)
) for _ in range(N)])

# Time of day categorization — 68% of fraud in Late Night
def get_time_of_day(ts):
    h = ts.hour
    if 5 <= h < 12:   return 'Morning'
    elif 12 <= h < 17: return 'Afternoon'
    elif 17 <= h < 21: return 'Evening'
    elif 21 <= h < 24: return 'Night'
    else:              return 'Late Night'

time_of_day = [get_time_of_day(ts) for ts in timestamps]

# Amounts — suspicious clustering at 4999 and 9999
def generate_amount(is_fraud_flag):
    if is_fraud_flag and random.random() < 0.30:
        return random.choice([4999, 9999])   # just-under-limit fraud amounts
    return round(random.uniform(10, 50000), 2)

# Determine fraud (bake in patterns)
devices_col = random.choices(device_types, weights=[0.65, 0.25, 0.10], k=N)
is_new_receiver = [random.random() < 0.20 for _ in range(N)]  # 20% new receivers
upi_app_col = random.choices(upi_apps, weights=app_weights, k=N)

is_fraud = []
for i in range(N):
    p = FRAUD_RATE
    if time_of_day[i] == 'Late Night':
        p *= 6.0    # 68% of fraud is Late Night
    if is_new_receiver[i]:
        p *= 5.0    # new receivers 5x more likely
    if devices_col[i] == 'Feature Phone':
        p *= 3.0    # 3x more vulnerable
    # Festive season spike (Oct-Nov)
    if timestamps[i].month in [10, 11]:
        p *= 1.8
    p = min(p, 0.95)
    is_fraud.append(1 if random.random() < p else 0)

# Ensure overall fraud rate is close to 3.2%
actual_rate = sum(is_fraud) / N
print(f"Pre-adjustment fraud rate: {actual_rate:.3f}")

amounts = [generate_amount(is_fraud[i]) for i in range(N)]

fraud_types = []
for f in is_fraud:
    if f == 0:
        fraud_types.append(None)
    else:
        ft = random.choices(
            ['Phishing', 'SIM Swap', 'Fake QR', 'Social Engineering', 'Account Takeover'],
            weights=[0.35, 0.20, 0.18, 0.15, 0.12]
        )[0]
        fraud_types.append(ft)

# Phishing spikes in Oct-Nov
for i in range(N):
    if is_fraud[i] and timestamps[i].month in [10, 11] and random.random() < 0.60:
        fraud_types[i] = 'Phishing'

# Transaction status — frauds often have Failed then Success pattern
def get_status(is_f, amount):
    if is_f:
        return random.choices(['Success', 'Failed', 'Reversed'], weights=[0.55, 0.25, 0.20])[0]
    return random.choices(['Success', 'Failed', 'Pending', 'Reversed'], weights=[0.85, 0.08, 0.04, 0.03])[0]

statuses = [get_status(is_fraud[i], amounts[i]) for i in range(N)]

sender_ids = [f'USR{str(random.randint(1000, 50000)).zfill(5)}' for _ in range(N)]
receiver_ids = []
for i in range(N):
    if is_new_receiver[i]:
        receiver_ids.append(f'USR{str(random.randint(80000, 99999)).zfill(5)}')
    else:
        receiver_ids.append(f'USR{str(random.randint(1000, 50000)).zfill(5)}')

sender_cities = random.choices(cities, k=N)
receiver_cities = []
for i in range(N):
    if is_fraud[i] and random.random() < 0.40:
        diff = [c for c in cities if c != sender_cities[i]]
        receiver_cities.append(random.choice(diff))
    else:
        receiver_cities.append(random.choice(cities))

df = pd.DataFrame({
    'transaction_id': [f'TXN{str(i+1).zfill(7)}' for i in range(N)],
    'timestamp': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
    'sender_id': sender_ids,
    'receiver_id': receiver_ids,
    'sender_city': sender_cities,
    'receiver_city': receiver_cities,
    'amount': amounts,
    'transaction_type': random.choices(
        transaction_types, weights=[0.35, 0.25, 0.20, 0.12, 0.08], k=N),
    'upi_app': upi_app_col,
    'time_of_day': time_of_day,
    'device_type': devices_col,
    'is_new_receiver': [int(x) for x in is_new_receiver],
    'is_fraud': is_fraud,
    'fraud_type': fraud_types,
    'transaction_status': statuses
})

df.to_csv('upi_transactions.csv', index=False)
print(f"Generated {len(df)} rows → upi_transactions.csv")
print(f"Actual fraud rate: {df['is_fraud'].mean():.3%}")
print("\nFraud by time of day:")
print(df[df['is_fraud']==1].groupby('time_of_day').size().sort_values(ascending=False))
