"""
Generates two CSVs:
  data/influencers_raw.csv      - 40 influencer campaign records
  data/partnerships_records.csv - structured deliverables / contract log
"""

import os, csv, random
from datetime import datetime, timedelta
import numpy as np

RNG = np.random.default_rng(42)
random.seed(42)

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Influencer pool ───────────────────────────────────────────────────────────
# (name, platform, tier, niche, followers, base_eng_rate, base_conv_rate, spend_usd)
INFLUENCERS = [
    # Instagram — Beauty/Fashion/Lifestyle
    ("Priya Sharma",       "Instagram", "Macro",  "Beauty",     820_000,  3.8, 2.1, 4200),
    ("Anjali Mehta",       "Instagram", "Micro",  "Skincare",    95_000,  6.2, 3.4, 1800),
    ("Ritu Kapoor",        "Instagram", "Mega",   "Fashion",  2_100_000,  2.1, 0.9, 9500),
    ("Neha Bose",          "Instagram", "Nano",   "Lifestyle",   18_000,  8.4, 4.8,  450),
    ("Kavita Reddy",       "Instagram", "Micro",  "Fitness",     72_000,  5.9, 3.1, 1400),
    ("Simran Gill",        "Instagram", "Macro",  "Food",       310_000,  4.3, 1.8, 3100),
    ("Meera Iyer",         "Instagram", "Micro",  "Travel",      58_000,  7.1, 2.9, 1100),
    ("Divya Nair",         "Instagram", "Nano",   "Beauty",      12_000,  9.2, 5.6,  300),
    ("Pooja Tiwari",       "Instagram", "Macro",  "Parenting",  480_000,  3.5, 1.6, 3800),
    ("Sanya Verma",        "Instagram", "Micro",  "Fashion",     88_000,  5.4, 2.7, 1600),
    # YouTube — Tech/Education/Gaming/Vlog
    ("Arjun Khanna",       "YouTube",   "Macro",  "Tech",       650_000,  4.2, 3.8, 5200),
    ("Rohit Bansal",       "YouTube",   "Mega",   "Gaming",   1_500_000,  3.6, 1.4, 8800),
    ("Vikram Singh",       "YouTube",   "Micro",  "Education",  140_000,  5.8, 4.2, 2200),
    ("Aditya Patel",       "YouTube",   "Macro",  "Finance",    720_000,  4.9, 5.1, 6100),
    ("Karan Malhotra",     "YouTube",   "Micro",  "Fitness",    185_000,  6.3, 3.9, 2800),
    ("Siddharth Roy",      "YouTube",   "Macro",  "Tech",       530_000,  3.8, 3.2, 4700),
    ("Nikhil Gupta",       "YouTube",   "Nano",   "Vlog",        22_000,  7.6, 2.8,  550),
    ("Rahul Desai",        "YouTube",   "Micro",  "Food",        96_000,  5.2, 2.4, 1700),
    ("Varun Joshi",        "YouTube",   "Macro",  "Travel",     410_000,  3.1, 1.9, 3600),
    ("Manish Tomar",       "YouTube",   "Micro",  "Education",  163_000,  6.7, 4.6, 2500),
    # TikTok — Entertainment/Fashion/Food
    ("Zara Khan",          "TikTok",    "Macro",  "Entertainment", 890_000, 7.8, 2.3, 3900),
    ("Aisha Malik",        "TikTok",    "Micro",  "Fashion",    210_000,  9.1, 3.7, 2100),
    ("Riya Chopra",        "TikTok",    "Mega",   "Comedy",   2_800_000,  6.4, 1.2, 11_000),
    ("Tanisha Bhatt",      "TikTok",    "Micro",  "Food",       175_000,  8.3, 3.2, 1900),
    ("Prachi Dubey",       "TikTok",    "Nano",   "Beauty",      31_000, 11.2, 5.8,  600),
    ("Sneha Rawat",        "TikTok",    "Macro",  "Fitness",    640_000,  7.2, 2.9, 3400),
    ("Nisha Pandey",       "TikTok",    "Micro",  "Dance",      125_000,  8.9, 2.1, 1500),
    ("Kritika Sen",        "TikTok",    "Macro",  "Lifestyle",  380_000,  6.8, 3.4, 2800),
    # Twitter/X — Finance/Tech/Marketing
    ("Sameer Ahuja",       "Twitter/X", "Macro",  "Finance",    520_000,  2.4, 4.8, 4400),
    ("Deepak Nair",        "Twitter/X", "Micro",  "Tech",        68_000,  3.1, 3.6, 1200),
    ("Ankit Sharma",       "Twitter/X", "Micro",  "Marketing",   45_000,  2.8, 2.9,  900),
    ("Rajesh Verma",       "Twitter/X", "Macro",  "Finance",    310_000,  2.1, 3.2, 3200),
    # LinkedIn — B2B/Career/Business
    ("Dr. Sunita Rao",     "LinkedIn",  "Micro",  "Career",      82_000,  4.6, 6.2, 1600),
    ("Neeraj Sharma",      "LinkedIn",  "Macro",  "B2B SaaS",   290_000,  3.9, 7.4, 3800),
    ("Pradeep Kulkarni",   "LinkedIn",  "Micro",  "Business",    64_000,  4.2, 5.8, 1300),
    ("Amit Srivastava",    "LinkedIn",  "Macro",  "Marketing",  340_000,  3.4, 6.1, 4200),
    # Extra cross-platform
    ("Isha Chauhan",       "Instagram", "Micro",  "Wellness",    78_000,  6.8, 3.3, 1500),
    ("Gaurav Mehta",       "YouTube",   "Micro",  "Personal Finance", 112_000, 5.5, 4.9, 1900),
    ("Luna Kapoor",        "TikTok",    "Micro",  "Skincare",   148_000,  9.4, 4.1, 1700),
    ("Harsh Bhatia",       "Twitter/X", "Micro",  "StartupLife",  38_000, 3.3, 3.8,  800),
]

CAMPAIGNS = [
    "Summer Glow Launch", "Festive Season Push", "New Year New You",
    "Monsoon Refresh", "Brand Awareness Q1", "Diwali Special",
]

BASE_DATE = datetime(2025, 10, 1)


def gen_influencers():
    rows = []
    for i, (name, platform, tier, niche, followers,
            base_eng, base_conv, spend) in enumerate(INFLUENCERS, 1):

        campaign = random.choice(CAMPAIGNS)
        days_ago  = RNG.integers(10, 120)
        camp_date = (BASE_DATE + timedelta(days=int(days_ago))).strftime("%Y-%m-%d")

        # Reach is a fraction of followers
        reach_rate = RNG.uniform(0.18, 0.55)
        reach      = int(followers * reach_rate)
        impressions= int(reach * RNG.uniform(1.4, 2.8))

        # Engagement rate with noise
        eng_rate = round(float(RNG.normal(base_eng, base_eng * 0.25)), 2)
        eng_rate = max(0.5, min(eng_rate, 18.0))

        # Clicks from reach × CTR
        ctr    = RNG.uniform(0.8, 4.5) / 100
        clicks = int(reach * ctr)

            # Conversions with noise — wider variance to create DROP/OPTIMIZE performers
        conv_rate = float(RNG.normal(base_conv, base_conv * 0.55))
        conv_rate = max(0.1, min(conv_rate, 12.0))
        conversions = max(1, int(clicks * conv_rate / 100))

        # Revenue: avg order value × conversions — realistic D2C values ($30–$110)
        aov_map   = {"Nano": 38, "Micro": 52, "Macro": 72, "Mega": 95}
        aov       = aov_map[tier] * RNG.uniform(0.65, 1.45)
        revenue   = round(float(aov * conversions), 2)

        # Spend with a little noise
        spend_f = round(float(spend * RNG.uniform(0.88, 1.12)), 2)

        rows.append({
            "influencer_id":   f"INF_{i:03d}",
            "influencer_name": name,
            "platform":        platform,
            "tier":            tier,
            "niche":           niche,
            "followers":       followers,
            "campaign":        campaign,
            "campaign_date":   camp_date,
            "reach":           reach,
            "impressions":     impressions,
            "engagement_rate": eng_rate,
            "clicks":          clicks,
            "conversions":     conversions,
            "spend_usd":       spend_f,
            "revenue_usd":     revenue,
        })

    path = os.path.join(DATA_DIR, "influencers_raw.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  Saved {len(rows)} influencer records -> {path}")
    return rows


DELIVERABLES_POOL = [
    "1x Reel + 3x Stories",
    "2x Feed Posts + 2x Stories",
    "1x YouTube Integration (60s)",
    "1x Dedicated YouTube Video",
    "3x TikToks",
    "5x Tweet Thread + Poll",
    "1x LinkedIn Article + 2x Posts",
    "2x Reels + 5x Stories + 1x Post",
    "1x YouTube Short + 1x Community Post",
]

STATUSES = ["Completed", "Completed", "Completed", "Live", "Pending Payment"]


def gen_partnerships(influencer_rows):
    rows = []
    for i, inf in enumerate(influencer_rows, 1):
        rows.append({
            "partnership_id":  f"PRT_{i:03d}",
            "influencer_name": inf["influencer_name"],
            "platform":        inf["platform"],
            "niche":           inf["niche"],
            "campaign":        inf["campaign"],
            "deliverables":    random.choice(DELIVERABLES_POOL),
            "fee_usd":         inf["spend_usd"],
            "posting_date":    inf["campaign_date"],
            "status":          random.choice(STATUSES),
            "contract_signed": "Yes",
            "notes":           "",
        })

    path = os.path.join(DATA_DIR, "partnerships_records.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  Saved {len(rows)} partnership records -> {path}")


if __name__ == "__main__":
    print("Generating data ...")
    rows = gen_influencers()
    gen_partnerships(rows)
    print("Done.")
