"""
Generates two synthetic CSVs:
  data/sales_data.csv  - 200 rows of D2C product sales (last 90 days)
  data/reviews.csv     - 60 customer reviews with mixed sentiment

Run once before the analysis scripts.
"""

import os, random, csv
from datetime import datetime, timedelta
import numpy as np

RNG = np.random.default_rng(42)
random.seed(42)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Product catalogue ─────────────────────────────────────────────────────────
PRODUCTS = [
    ("Whey Protein Shake 1kg",        "Nutrition",    1299),
    ("Collagen Powder 300g",           "Nutrition",     999),
    ("Vitamin C Effervescent 60ct",    "Nutrition",     399),
    ("Omega-3 Fish Oil 90 Caps",       "Nutrition",     599),
    ("Glow Face Serum 30ml",           "Beauty",       1499),
    ("Hydrating Lip Balm SPF30",       "Beauty",        249),
    ("Natural Body Lotion 200ml",      "Beauty",        499),
    ("Rose Water Toner 150ml",         "Beauty",        349),
    ("Yoga Mat Premium 6mm",           "Fitness",      1199),
    ("Resistance Bands Set 5-pack",    "Fitness",       799),
    ("Adjustable Dumbbells 10kg Pair", "Fitness",      2499),
    ("Foam Roller Deep Tissue",        "Fitness",       699),
    ("Lavender Essential Oil 15ml",    "Wellness",      599),
    ("Sleep Gummies Melatonin 60ct",   "Wellness",      499),
    ("Bamboo Diffuser + 2 Oils",       "Wellness",      849),
    ("Herbal Immunity Kadha 500ml",    "Wellness",      299),
]

TODAY = datetime.today()

# ── Sales data ────────────────────────────────────────────────────────────────
SALES_PATH = os.path.join(DATA_DIR, "sales_data.csv")

def gen_sales():
    rows = []
    for _ in range(200):
        product, category, base_price = random.choice(PRODUCTS)
        days_ago      = RNG.integers(1, 91)
        date          = (TODAY - timedelta(days=int(days_ago))).strftime("%Y-%m-%d")
        discount_pct  = int(RNG.choice([0, 5, 10, 15, 20, 25, 30, 40],
                                        p=[0.20, 0.10, 0.20, 0.15, 0.15, 0.08, 0.07, 0.05]))
        price         = round(base_price * RNG.uniform(0.95, 1.05), 0)
        units_sold    = int(RNG.integers(3, 120))
        effective_price = price * (1 - discount_pct / 100)
        revenue       = round(effective_price * units_sold, 2)
        rows.append({
            "date":         date,
            "product":      product,
            "category":     category,
            "price":        price,
            "discount_pct": discount_pct,
            "units_sold":   units_sold,
            "revenue":      revenue,
        })

    with open(SALES_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Saved {len(rows)} rows -> {SALES_PATH}")

# ── Customer reviews ──────────────────────────────────────────────────────────
REVIEWS_PATH = os.path.join(DATA_DIR, "reviews.csv")

REVIEW_TEMPLATES = [
    # Positive
    ("Whey Protein Shake 1kg",        "positive", "Amazing product! Mixability is great and the chocolate flavour is not too sweet. Noticed muscle recovery improvement within 2 weeks. Will definitely reorder."),
    ("Glow Face Serum 30ml",          "positive", "My skin has never looked this good. After 3 weeks the dark spots are visibly lighter. Packaging is elegant too. Worth every rupee."),
    ("Yoga Mat Premium 6mm",          "positive", "Perfect thickness, non-slip grip even during hot yoga. My old mat used to slide everywhere. This is a game changer for my practice."),
    ("Sleep Gummies Melatonin 60ct",  "positive", "Finally sleeping through the night! Tastes like berries and actually works within 30 minutes. No groggy feeling the next morning."),
    ("Resistance Bands Set 5-pack",   "positive", "Great quality for the price. The bands don't snap or roll up mid-workout. All 5 resistance levels are genuinely useful."),
    ("Lavender Essential Oil 15ml",   "positive", "Smells exactly like real lavender, not artificial. A few drops in my diffuser and the whole room is calming. Will buy again."),
    ("Vitamin C Effervescent 60ct",   "positive", "Love the orange flavour. Dissolves in 30 seconds, no residue. I've been taking it daily and my energy levels feel noticeably better."),
    ("Natural Body Lotion 200ml",     "positive", "Light, absorbs quickly, no greasy feeling. My dry elbows are completely healed after 10 days of use. Lovely subtle scent too."),
    ("Collagen Powder 300g",          "positive", "Mixes well into my morning coffee and has no weird taste. Skin feels more plump. Too early to judge nails but optimistic so far."),
    ("Bamboo Diffuser + 2 Oils",      "positive", "Beautiful diffuser, looks premium, whisper quiet. The oils that came with it are genuinely good quality. Perfect gift idea."),
    ("Foam Roller Deep Tissue",       "positive", "Exactly what I needed post leg-day. The ridges hit the right spots. Feels durable and high-density, not hollow like cheap rollers."),
    ("Rose Water Toner 150ml",        "positive", "Refreshing! I use it morning and night and my skin barrier has improved noticeably. No alcohol, no irritation. Repurchased twice."),
    ("Hydrating Lip Balm SPF30",      "positive", "Finally a lip balm that actually moisturises and has SPF. Doesn't leave a white cast. Carrying it everywhere now."),
    ("Omega-3 Fish Oil 90 Caps",      "positive", "No fishy aftertaste which was my main concern. Easy to swallow capsule. Joints feel better after 3 weeks of use."),
    ("Adjustable Dumbbells 10kg Pair","positive", "Build quality is excellent. The adjustment mechanism is smooth and secure. Saved so much space compared to a full rack."),
    ("Herbal Immunity Kadha 500ml",   "positive", "Tastes exactly like homemade kadha, not watered down. I drink it when I feel a cold coming and it helps every time."),
    # Negative
    ("Whey Protein Shake 1kg",        "negative", "Clumpy even with a blender bottle. Took 2 weeks to arrive and the seal was broken. Customer support hasn't responded in 4 days. Very disappointing."),
    ("Glow Face Serum 30ml",          "negative", "Broke me out badly within 3 days. Checked ingredients and it has a fragrance I'm allergic to — not mentioned clearly on the listing. Returned it."),
    ("Yoga Mat Premium 6mm",          "negative", "Starts slipping after 20 minutes of sweating. The 'non-slip' claim is completely false for hot workouts. Returned, very disappointed."),
    ("Sleep Gummies Melatonin 60ct",  "negative", "No effect at all even after 2 weeks. I took 2 gummies as instructed and still couldn't sleep. Feel like I wasted ₹500. Not reordering."),
    ("Resistance Bands Set 5-pack",   "negative", "The heaviest band snapped during my first use. Nearly hit my face. This is a safety hazard. Demanded a full refund."),
    ("Adjustable Dumbbells 10kg Pair","negative", "One side arrived cracked. The replacement took 3 weeks and that one had a loose adjustment dial. Quality control is clearly very poor."),
    ("Natural Body Lotion 200ml",     "negative", "The pump dispenser broke after 2 uses, now I have to unscrew the cap every time. The lotion itself is fine but the packaging is terrible."),
    ("Collagen Powder 300g",          "negative", "Tastes awful — chalky and leaves a bitter aftertaste in coffee. Tried mixing with smoothie, still undrinkable. Would not recommend."),
    ("Bamboo Diffuser + 2 Oils",      "negative", "Stopped working after 10 days. The LED ring just went out. Customer support offered a 20% discount on next order instead of a replacement. Unacceptable."),
    ("Herbal Immunity Kadha 500ml",   "negative", "The bottle leaked in transit, arrived half-empty. No response from support after 5 days. Paid for 500ml, received maybe 200ml. Fraud."),
    ("Hydrating Lip Balm SPF30",      "negative", "Leaves a white cast that looks terrible on darker skin tones. Wish the product page had shown this. Packaging is also very cheap for the price."),
    ("Vitamin C Effervescent 60ct",   "negative", "Received an expired batch — expiry was 2 months ago. This is a health product, this is unacceptable. Please check your inventory management."),
    # Neutral
    ("Whey Protein Shake 1kg",        "neutral",  "Decent product. Does what it says on the label. Delivery was on time. I've had better tasting proteins but this is good value for money."),
    ("Glow Face Serum 30ml",          "neutral",  "It's okay. No irritation and the texture is nice, but I haven't seen dramatic results after 3 weeks. Maybe needs longer. Packaging could be improved."),
    ("Yoga Mat Premium 6mm",          "neutral",  "Average mat. Good for light yoga but starts slipping a bit in intense sessions. For the price I expected better non-slip technology."),
    ("Resistance Bands Set 5-pack",   "neutral",  "Fine for beginners. The lightest two bands are useful, the heaviest three feel identical to me. Instructions would have been helpful."),
    ("Omega-3 Fish Oil 90 Caps",      "neutral",  "Too early to say if it works. No negative effects after a week. Capsule size is on the larger side but manageable. Will update after a month."),
    ("Lavender Essential Oil 15ml",   "neutral",  "Decent quality oil. The scent is authentic but fades quite fast in my diffuser. Expected it to last longer. Delivery was prompt though."),
    ("Foam Roller Deep Tissue",       "neutral",  "Does the job. A bit lighter than I expected, not sure how long it will last with daily use. No major complaints, just not 'wow'."),
    ("Sleep Gummies Melatonin 60ct",  "neutral",  "Works sometimes, not others. The taste is nice. Hard to tell if it's the gummies or just placebo at this point. Will give it another week."),
    ("Rose Water Toner 150ml",        "neutral",  "Nice scent and feels refreshing but I can't say my skin looks dramatically different after 2 weeks. Maybe I'm using it wrong."),
    ("Collagen Powder 300g",          "neutral",  "No strong taste which is good. Mixing is fine. Too early to see skin results. Would be helpful if the brand shared more evidence/studies."),
    ("Herbal Immunity Kadha 500ml",   "neutral",  "Average for the price. Tastes herbal but not as strong as I wanted. Did seem to help when I had a cold but hard to be sure."),
    ("Natural Body Lotion 200ml",     "neutral",  "Texture is nice but the fragrance is stronger than I prefer. Skin does feel softer. Nothing revolutionary but a decent everyday lotion."),
]

def gen_reviews():
    rows = []
    for i, (product, sentiment, text) in enumerate(REVIEW_TEMPLATES, 1):
        rows.append({
            "review_id": i,
            "product":   product,
            "sentiment_label": sentiment,
            "review_text": text,
        })
    with open(REVIEWS_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Saved {len(rows)} rows -> {REVIEWS_PATH}")

if __name__ == "__main__":
    print("Generating synthetic data ...")
    gen_sales()
    gen_reviews()
    print("Done.")
