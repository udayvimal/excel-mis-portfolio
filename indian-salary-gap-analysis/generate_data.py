import pandas as pd
import numpy as np
import random
import string

np.random.seed(42)
random.seed(42)

N = 8000

# Indian name components
first_names_male = ['Rahul', 'Amit', 'Vikram', 'Arjun', 'Rohit', 'Karan', 'Aditya', 'Manish',
                    'Sanjay', 'Deepak', 'Suresh', 'Rajesh', 'Nikhil', 'Aman', 'Prateek',
                    'Varun', 'Harsh', 'Ankit', 'Gaurav', 'Mohit']
first_names_female = ['Priya', 'Anjali', 'Neha', 'Sneha', 'Pooja', 'Divya', 'Riya', 'Kavya',
                      'Shruti', 'Ananya', 'Simran', 'Nisha', 'Megha', 'Swati', 'Shweta',
                      'Pallavi', 'Isha', 'Tanvi', 'Ritika', 'Aishwarya']
last_names = ['Sharma', 'Verma', 'Gupta', 'Singh', 'Kumar', 'Patel', 'Shah', 'Mehta',
              'Joshi', 'Nair', 'Reddy', 'Rao', 'Iyer', 'Pillai', 'Chatterjee',
              'Das', 'Malhotra', 'Kapoor', 'Bose', 'Murthy']

cities = ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Pune', 'Chennai', 'Noida', 'Gurgaon']
city_multiplier = {'Bangalore': 1.35, 'Mumbai': 1.30, 'Delhi': 1.25, 'Hyderabad': 1.20,
                   'Gurgaon': 1.22, 'Pune': 1.10, 'Noida': 1.05, 'Chennai': 1.00}

company_types = ['MNC', 'Indian Startup', 'Indian Corporate', 'PSU', 'SME']
ct_multiplier = {'MNC': 1.40, 'Indian Startup': 1.15, 'Indian Corporate': 1.00, 'PSU': 0.85, 'SME': 0.75}

industries = ['IT', 'Finance', 'EdTech', 'HealthTech', 'Ecommerce', 'Manufacturing', 'Consulting']
ind_multiplier = {'IT': 1.20, 'Finance': 1.30, 'EdTech': 0.90, 'HealthTech': 0.95,
                  'Ecommerce': 1.05, 'Manufacturing': 0.85, 'Consulting': 1.15}

job_roles = ['Data Analyst', 'Software Engineer', 'Product Manager', 'HR', 'Marketing', 'Operations', 'Finance Analyst']
role_base = {'Data Analyst': 6.5, 'Software Engineer': 7.0, 'Product Manager': 10.0,
             'HR': 5.0, 'Marketing': 5.5, 'Operations': 5.0, 'Finance Analyst': 6.0}

education_levels = ['BTech', 'MBA', 'BSc', 'BA', 'MTech', 'PhD']
edu_multiplier = {'BTech': 1.10, 'MBA': 1.25, 'BSc': 0.95, 'BA': 0.85, 'MTech': 1.20, 'PhD': 1.35}

company_sizes = ['Startup', 'Mid', 'Large', 'Enterprise']
remote_options = ['Yes', 'Partial', 'No']

genders = []
for _ in range(N):
    g = random.choices(['Male', 'Female', 'Other'], weights=[0.60, 0.37, 0.03])[0]
    genders.append(g)

names = []
for g in genders:
    if g == 'Male':
        names.append(f"{random.choice(first_names_male)} {random.choice(last_names)}")
    elif g == 'Female':
        names.append(f"{random.choice(first_names_female)} {random.choice(last_names)}")
    else:
        fn = random.choice(first_names_male + first_names_female)
        names.append(f"{fn} {random.choice(last_names)}")

ages = np.random.randint(22, 56, N)
experience_years = np.clip(ages - 22 - np.random.randint(0, 4, N), 0, 25)

cities_col = random.choices(cities, k=N)
company_types_col = random.choices(company_types, weights=[0.25, 0.25, 0.20, 0.15, 0.15], k=N)
industries_col = random.choices(industries, weights=[0.30, 0.15, 0.12, 0.08, 0.12, 0.13, 0.10], k=N)
roles_col = random.choices(job_roles, weights=[0.18, 0.28, 0.12, 0.10, 0.10, 0.12, 0.10], k=N)
education_col = random.choices(education_levels, weights=[0.35, 0.20, 0.15, 0.10, 0.12, 0.08], k=N)
company_size_col = random.choices(company_sizes, weights=[0.25, 0.30, 0.25, 0.20], k=N)
remote_col = random.choices(remote_options, weights=[0.30, 0.40, 0.30], k=N)

base_salaries = []
bonuses = []
total_ctcs = []

for i in range(N):
    role = roles_col[i]
    exp = experience_years[i]
    city = cities_col[i]
    ct = company_types_col[i]
    ind = industries_col[i]
    edu = education_col[i]
    gender = genders[i]

    # Base from role
    base = role_base[role]
    # Experience curve
    if role == 'Data Analyst':
        if exp <= 2:   base = random.uniform(5.5, 8.0)
        elif exp <= 4: base = random.uniform(10.0, 18.0)
        elif exp <= 7: base = random.uniform(18.0, 28.0)
        else:          base = random.uniform(25.0, 40.0)
    else:
        base = base + exp * random.uniform(0.8, 1.8)

    base *= city_multiplier[city]
    base *= ct_multiplier[ct]
    base *= ind_multiplier[ind]
    base *= edu_multiplier[edu]

    # Gender pay gap — female 18% lower in same role+exp
    if gender == 'Female':
        base *= random.uniform(0.78, 0.86)   # avg ~18% lower
    elif gender == 'Other':
        base *= random.uniform(0.88, 0.95)

    # Remote premium
    if remote_col[i] == 'Yes':
        base *= random.uniform(1.05, 1.12)

    base = round(base + random.uniform(-0.5, 0.5), 2)
    bonus = round(base * random.uniform(0.05, 0.25), 2)
    total = round(base + bonus, 2)

    base_salaries.append(max(base, 2.5))
    bonuses.append(max(bonus, 0.1))
    total_ctcs.append(max(total, 3.0))

df = pd.DataFrame({
    'employee_id': [f'EMP{str(i+1).zfill(5)}' for i in range(N)],
    'name': names,
    'age': ages,
    'gender': genders,
    'city': cities_col,
    'company_type': company_types_col,
    'industry': industries_col,
    'job_role': roles_col,
    'experience_years': experience_years,
    'education': education_col,
    'base_salary_lpa': base_salaries,
    'bonus_lpa': bonuses,
    'total_ctc_lpa': total_ctcs,
    'remote_work': remote_col,
    'company_size': company_size_col
})

df.to_csv('india_salaries.csv', index=False)
print(f"Generated {len(df)} rows → india_salaries.csv")
print("\nGender pay gap:")
print(df.groupby('gender')['total_ctc_lpa'].mean().round(2))
print("\nCity salary comparison:")
print(df.groupby('city')['total_ctc_lpa'].median().sort_values(ascending=False).round(2))
