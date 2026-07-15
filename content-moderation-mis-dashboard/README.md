# Content Moderation Operations MIS Dashboard

A fully-built portfolio project demonstrating the data analysis, Excel formula work, and operational reporting skills required for a **Trust & Safety / Operations Analyst** role. Built to model a real-world content moderation workflow at scale (14,400+ daily records, 20 moderators, 8 content categories, 90 days).

> **Dataset is simulated** — generated via Python with realistic variance, deliberate patterns, and seeded randomness to allow reproducible findings.

---

## Quick Start

```bash
pip install pandas numpy openpyxl
python build_dashboard.py
# Outputs:
#   data/moderation_data_90day.csv       (14,400 rows)
#   excel/content_moderation_mis_dashboard.xlsx
```

Open the `.xlsx` in Excel 365 (or Excel 2019+). All formulas calculate live on open — nothing is hardcoded in the summary sheets.

---

## What's Inside

### File Structure
```
content-moderation-mis-dashboard/
├── build_dashboard.py          # Generates data + builds the full Excel workbook
├── data/
│   └── moderation_data_90day.csv
├── excel/
│   └── content_moderation_mis_dashboard.xlsx
├── report/
│   └── trend_analysis.md       # One-page management report
└── README.md
```

### Dataset Fields
| Field | Description |
|---|---|
| Date | 90 days: Jan 1 – Mar 31, 2026 |
| Moderator_ID | MOD_001 to MOD_020 (20 moderators) |
| Content_Category | Hate Speech, Violence, Nudity, Spam, Misinformation, Child Safety, Bullying, Self-Harm |
| Videos_Reviewed | Daily count per moderator per category; realistic Poisson distribution |
| Avg_Review_Time_Sec | Category-dependent (Child Safety: ~300s baseline, Spam: ~60s) |
| False_Positives / False_Negatives | Small percentage of reviewed volume; varies by category |
| Escalations | Higher for sensitive categories (Child Safety: 6%, Self-Harm: 5%) |
| SLA_Target_Pct | 95% — standard content moderation SLA |
| SLA_Breaches | Count of items reviewed outside SLA window |
| SLA_Compliance_Pct | `(1 − breaches/volume) × 100` |
| Status | Derived: Critical / Warning / Healthy |

**Deliberate patterns built into the data:**
- **Monday surge** — volume +40%, SLA breach rate spikes to ~12% (vs. 4% baseline)
- **Incident window Feb 4–8** — volume +80%, breach rate climbs to ~20%
- **Weekend dip** — volume ~30% lower, sets up Monday backlog accumulation

---

## Excel Workbook — Sheet-by-Sheet

### Sheet 1: Raw_Data
Full 14,400-row dataset. Header frozen, column widths set. Conditional formatting on the `Status` column: **red = Critical**, **yellow = Warning**, **green = Healthy**.

### Sheet 2: Moderator_Summary
Aggregates each of 20 moderators across the full 90-day period using live formulas:

| Formula | Purpose |
|---|---|
| `SUMIF(Raw_Data!$B:$B, A2, Raw_Data!$D:$D)` | Total videos reviewed per moderator |
| `AVERAGEIF(Raw_Data!$B:$B, A2, Raw_Data!$E:$E)` | Average review time per moderator |
| `SUMIF(...)` × 2 | Total false positives and false negatives |
| `IFERROR((D+E)/B*100, 0)` | Computed error rate % |
| **Nested IF (4-tier)** | `=IF(H>=97,"Top Performer",IF(H>=93,"Standard",IF(H>=88,"Needs Review","At Risk")))` |

Conditional formatting flags "Top Performer" (green) and "At Risk" (red) rows automatically.

### Sheet 3: Category_Breakdown
SUMIF / AVERAGEIF breakdown by content category — volume, review time, error rate, escalations, SLA compliance. Reveals that **Child Safety** has the longest average review time (~300s) and highest escalation rate, while **Spam** is fastest (~60s) with the lowest escalation volume.

### Sheet 4: MIS_Report
Day-by-day pivot-table equivalent (90 rows, one per date). Uses:
- `SUMIF` — aggregate daily volume, breaches, escalations, and errors from Raw_Data
- `AVERAGEIF` — compute daily average SLA compliance
- `WEEKNUM(DATEVALUE(...), 1)` — week-number column enabling weekly rollups
- `TEXT(DATEVALUE(...), "DDD")` — human-readable day-of-week label
- **Nested IF** for daily Status_Flag
- **Traffic-light conditional formatting** on SLA Compliance %: red (<90), yellow (90–94.99), green (≥95)

### Sheet 5: Dashboard
Summary view for management. Contains:

**KPI Banner (6 metrics):**
- Total Videos Reviewed — `=SUM(Raw_Data!D:D)`
- Overall SLA Compliance % — `=ROUND(AVERAGE(Raw_Data!K:K),1)`
- Avg Error Rate %, Escalation Rate %, Avg Review Time, Active Moderators

**30-Day Trend Table:**
- Uses **XLOOKUP** to pull daily stats from MIS_Report: `=XLOOKUP(date, MIS_Report!$A:$A, MIS_Report!$D:$D, 0)`
- Traffic-light conditional formatting on SLA compliance and Status columns
- Nested IF for row-level status

**Data Validation Dropdown:**
- Category filter dropdown (H9) — built with `DataValidation` in openpyxl, selectable list: All Categories, Hate Speech, Violence, … Self-Harm

**Two Embedded Charts:**
1. **Bar chart** — Weekly video review volume (13 weeks), data sourced from SUMPRODUCT weekly rollup formulas
2. **Line chart** — Average weekly SLA compliance %, y-axis floored at 80% to amplify variance

---

## Key Finding & Recommendation

**Finding:** SLA compliance drops from ~96% (normal weekday baseline) to ~88% every Monday due to weekend queue accumulation, and crashes to ~80% during the five-day February incident window — five times the normal breach rate.

**Recommendation:** Three actions were identified in the trend analysis:
1. **Staggered Sunday–Monday shift overlap** to pre-clear the weekend backlog before Monday's peak
2. **Dynamic priority routing** triggered when daily volume exceeds 110% of the 7-day rolling average (Child Safety and Self-Harm prioritized; Spam processed in parallel)
3. **Pre-incident buffer protocol** — proactively clear backlog to <50% capacity on consecutive Warning days to create headroom before surges hit

Full write-up with quantified impact: [`report/trend_analysis.md`](report/trend_analysis.md)

---

## Formulas & Techniques (Recruiter Reference)

| Technique | Where Used |
|---|---|
| `SUMIF` / `AVERAGEIF` | Moderator_Summary, Category_Breakdown, MIS_Report |
| `SUMIFS` / `SUMPRODUCT` | Dashboard weekly rollups (multi-condition aggregation) |
| `XLOOKUP` | Dashboard trend table — cross-sheet metric lookup |
| **Nested IF (4 levels)** | Moderator_Summary `Performance_Tier`; MIS_Report & Dashboard `Status_Flag` |
| `WEEKNUM` + `TEXT` + `DATEVALUE` | MIS_Report week/day labeling |
| `IFERROR` | All computed ratio columns (zero-division protection) |
| Conditional Formatting | Traffic-light SLA colours on Raw_Data, MIS_Report, Dashboard |
| Data Validation Dropdown | Dashboard category filter (H9) |
| Embedded Charts (Bar + Line) | Dashboard weekly volume and SLA trend |
| Frozen Panes | All four data sheets |
| Tab Colour Coding | Each sheet has a distinct colour for navigation |

---

## Tech Stack
- **Python 3.10+** — data generation (NumPy, Pandas) and Excel build (openpyxl)
- **Excel 365 / Excel 2019+** — required for XLOOKUP; all other formulas work in Excel 2016+
- No BI tools, no macros — pure formula-driven workbook

---

*Built as a portfolio project for a Trust & Safety / Operations Analyst Intern application (ByteDance / TikTok). Simulated dataset only.*
