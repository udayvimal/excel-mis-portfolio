# Simulated User Feedback: Pain Point Synthesis

> **Transparency note — please read first**
>
> This is a **self-designed case study exercise**. These quotes are not from real user interviews
> conducted with an actual company's customers. They are plausible, realistic pain points I wrote
> from first-principles — drawing on publicly available knowledge of youth fintech UX challenges,
> common payment failure patterns, and typical teen user behaviour — and then explicitly cross-validated
> against the quantitative patterns in the synthetic dataset. This section is included to demonstrate
> how a product analyst translates qualitative signals into data-backed decisions, not to claim
> primary research authority.

---

## Mock User Quotes

The quotes span 4 user archetypes: **First-time Struggling Users** (ages 13-15, new to UPI),
**Teen Power Users** (ages 16-19, high transaction frequency), **Parental Control Users**
(ages 11-13, heavy top-up, parent-managed limits), and **Casual Users**
(ages 14-18, low frequency, mainly peer transfers).

---

### 1. "My payment just… failed. I have no idea why."
**Profile:** Arjun, 15 | First-time user, attempted UPI payment to a food vendor

> "I downloaded the app, added my money, and tried to pay at the canteen. It said 'Payment failed'
> but didn't tell me what to do next. I thought my money was gone. I showed my friend and he said
> I probably hadn't linked my bank account properly. Why didn't it just tell me that?"

**Data link:**
The quantitative data shows a **30.7% failure rate on first-time UPI transactions** — more than 3× the
repeat UPI failure rate of 9.1%. This is the single largest failure spike in the dataset. Of the 580 users
in the cohort, every user who attempted UPI as their first transaction had nearly a 1-in-3 chance of failing.
The drop-off from ambiguous error messaging (no root cause shown → user doesn't know how to retry) is a
primary driver of the **51 percentage-point churn gap** between users whose first transaction succeeded
vs failed (92.1% retention vs 41.2%).

---

### 2. "It failed and I just... stopped using it for a while."
**Profile:** Sneha, 14 | Attempted peer transfer, got a "declined" status

> "The payment declined and I was kind of embarrassed because I was trying to pay my friend back.
> I didn't try again for a few weeks. It just felt unreliable. I use my sister's PhonePe now."

**Data link:**
Of users whose first transaction was not successful, only **41.2% made a second transaction** — vs
**92.1%** of users whose first transaction succeeded. This 51pp retention gap is the sharpest signal
in the entire dataset. The 98 single-transaction users in the cohort skew heavily toward those who
experienced a failure or decline on their first session.

---

### 3. "I didn't even know there was a limit set by my parents."
**Profile:** Rahul, 12 | Low-activity user, top-up feature

> "My mom said she'd set a spending limit but I couldn't find it anywhere in the app. I tried to
> pay ₹500 at a shop and it got declined. I didn't know it was the limit until I called her. I just
> thought the app was broken."

**Data link:**
The "spending limit set by parent" feature has only **26.0% adoption** (151 out of 580 users),
despite being a core value proposition for the 11-14 segment (255 users, 44% of the cohort).
This low penetration suggests the feature is not being discovered organically. Combined with the
**5.9% Card Top-up failure rate** — some fraction of which may be limit-related declines misread as
errors — this indicates a discoverability gap that also generates misleading error experiences for
young users.

---

### 4. "Bill splitting is confusing — I gave up and just Venmo'd them separately."
**Profile:** Priya, 17 | Active user, peer transfer + group expenses

> "I tried to do a bill split after dinner with four friends. I couldn't figure out who gets
> charged what, and one of my friends doesn't even have the app. I ended up doing separate
> payments instead. The feature felt unfinished."

**Data link:**
Bill Split has a **20.4% failure rate** — the highest of any transaction type, and nearly 2× the
platform average. Yet it has **42.4% adoption** (246 users have tried it at least once), meaning
the feature is being discovered but is failing users at a disproportionate rate. This is a "broken
promise" pattern: the feature attracts users but doesn't deliver, creating frustration rather than
loyalty. Each failed bill split is also a peer-visibility moment (friends watching the payer struggle),
making it a trust-damaging event.

---

### 5. "I keep getting cashback notifications but I never know how to check my actual rewards."
**Profile:** Kiran, 16 | Medium-frequency user, engaged but confused

> "I get these popups that say I earned ₹3 cashback but when I go to the rewards section, the
> numbers never match what I expected. I don't know if I'm redeeming them or if they just expire.
> I don't check it anymore."

**Data link:**
"Rewards" feature adoption sits at **37.8%** (219 users) while "cashback tracker" is at **35.7%**
(207 users) — both comfortably used, but neither dominates. The data shows that 15-19 year-olds
(higher amounts, avg ₹305 per transaction) have more to gain from cashback, yet the cohort analysis
shows the 15-19 group also has a slightly **lower success rate (86.1%)** vs 11-14 (89.1%), potentially
reflecting more complex transaction types (UPI, peer transfer) with higher failure exposure. Opaque
reward tracking adds friction to a feature that should be a retention driver.

---

### 6. "The app is slow when I'm trying to pay — and that makes me nervous."
**Profile:** Divya, 18 | Heavy user, 15+ transactions

> "Sometimes I'm at a shop and the loading takes like 8 seconds to confirm the payment. The
> merchant is staring at me. I've had payments go through twice because I tapped again.
> It makes me anxious to use it in public."

**Data link:**
The average **app session length is 7.8 minutes** for 11-14 users and 7.6 minutes for 15-19 users.
Notably, sessions following a **failed or declined transaction are 20–60% longer** (as captured in
the synthetic data's session length model) — users stay in the app trying to troubleshoot rather
than completing a smooth transaction. Elevated session length after failure is a proxy for confusion
and frustration, not engagement.

---

### 7. "I didn't know I had to link a bank account first — I thought topping up was enough."
**Profile:** Meera, 13 | New user, first-week churn

> "I added ₹200 to the card from my dad's account. I thought I could pay anywhere with that.
> But when I tried to do a UPI payment, it kept asking me to link a bank account.
> I didn't have one. I just use it like a prepaid card now."

**Data link:**
Card Top-up has the **lowest failure rate (5.9%)** of all transaction types and is the most-used
feature among 11-14 users (avg ₹134 per transaction vs ₹305 for older teens). The UPI pathway,
however, requires an additional bank linkage step that the top-up flow does not. This creates a
two-class user experience: younger users who succeed on the card flow but hit a wall on UPI, which
explains why the **first-time UPI failure rate (30.7%)** is concentrated in users who have no
prior bank-linking experience — often the younger cohort.

---

### 8. "My friends send me money via other apps because not everyone has this one."
**Profile:** Aditya, 16 | Peer Transfer user

> "I can only use send money if my friend also has the app. My cousin doesn't have it so I always
> have to switch to UPI on my regular bank app. It would be easier if I could just send to any UPI ID."

**Data link:**
"Split with friends" adoption (42.4%) and "send money" adoption (67.9%) represent the two most
used features in the app — but both depend on peer adoption. The data shows Peer Transfer has a
**10.2% failure rate**, higher than Card Top-up (5.9%), and the 15-19 cohort (more peer-transfer
activity, avg ₹305 transactions) is most exposed to this. Network dependency is a structural
ceiling on engagement that the data alone cannot solve — but interoperability with any UPI ID
would expand the addressable peer network and reduce friction-driven abandonment.

---

### 9. "I got charged but the payment didn't go through — and I still don't know why."
**Profile:** Vikram, 15 | Occasional user, dropped off after confusion

> "I transferred ₹100 to a friend and it said 'processing.' I waited and then it said failed.
> But ₹100 was gone from my balance for two days. I called my dad and we were both confused.
> He told me not to use it anymore."

**Data link:**
The dataset captures "declined" status as a distinct failure mode from "failed" (split roughly
55%/45% in the simulation's failure allocation). Declined transactions are often bank-side rejections
that still initiate temporary holds. The 30.7% first-time UPI failure rate includes both categories,
meaning roughly 14-16% of first-time UPI users likely see a "processing then failed" ambiguous
state — a pattern that drives parent intervention and household-level trust damage, affecting
long-term app adoption in the 11-14 segment.

---

### 10. "I wish the app could show me what I spent money on, like a mini statement."
**Profile:** Anjali, 17 | Active, rewards-aware user

> "I'd love to see how I spent each month — like how much on food, how much on friends. My mom
> asked me to track my expenses and I couldn't easily show her. I had to screenshot everything.
> If this app had that, I wouldn't need to use anything else."

**Data link:**
The 15-19 cohort averages **₹305 per transaction** and **4.8 transactions per user** — nearly 2.3×
the per-transaction amount of the 11-14 group. Higher spenders with higher frequency are the natural
market for spending insights / categorisation tools. The "cashback tracker" and "rewards" features
have ~35-38% adoption but offer backward-looking point tracking rather than forward-looking
spend visibility. A spending summary view could increase monthly active user retention by giving
older teen users a reason to open the app even between transactions.

---

## Quote → Data Mapping Summary

| # | Quote Theme | Data Signal | Severity |
|---|---|---|---|
| 1 | First UPI failure, no error explanation | 30.7% first-UPI fail rate | Critical |
| 2 | Abandoned after declined payment | 51pp retention gap (41% vs 92%) | Critical |
| 3 | Spending limit undiscoverable | 26% adoption for a core parental feature | High |
| 4 | Bill Split feels unfinished | 20.4% bill split failure rate, highest in portfolio | High |
| 5 | Cashback tracking opaque | Rewards at 37.8% but no clear conversion clarity | Medium |
| 6 | Slow confirmation = anxiety | Session length spikes 20–60% after failed tx | Medium |
| 7 | Top-up ≠ UPI (confused onboarding) | 5.9% top-up fail vs 30.7% first-UPI fail (5× gap) | Critical |
| 8 | Peer dependency limits network reach | Peer Transfer 10.2% fail; UPI interop gap | High |
| 9 | Ambiguous processing state (temp hold) | ~14–16% of first-UPI attempts hit ambiguous state | High |
| 10 | No spending categorisation / summary | 15–19 cohort: ₹305 avg, 4.8 tx/user — high-value segment |Medium |
