# AML MIS Data Quality & Validation Notes
**Dataset:** 120-day AML monitoring period (Jan–Apr 2026)
**Prepared by:** Reporting Analytics | Date: 2026-07-12

---

## Data Quality Checks Performed

### Check 1: Orphaned Alert Records
**Issue:** Alerts referencing Transaction_IDs not present in the transactions table.
**Detection formula:** `COUNTIF(Raw_Transactions!$A:$A, Raw_Alerts!B2) = 0`
**Findings:** **10 orphaned alert records** identified. These alerts (TXN_ORPHAN_000 to TXN_ORPHAN_009) cannot be linked to a source transaction, making disposition investigation impossible.
**Remediation:** Escalate to source system owners; check if transactions were purged before alert log export.

### Check 2: Duplicate Transaction Records
**Issue:** Multiple Transaction_IDs with identical Customer_ID, Date, and Amount (near-duplicate pattern).
**Detection formula:** `COUNTIFS($B:$B,B2,$C:$C,C2,$D:$D,D2)>1`
**Findings:** **5 near-duplicate records** found — same customer, same date, same amount. These may represent double-posted entries or batch processing errors.
**Remediation:** Deduplicate based on Customer_ID + Date + Amount combination; retain earliest Transaction_ID.

### Check 3: Missing Customer Risk Profiles
**Issue:** Transactions from customers with no corresponding entry in the Risk Profile table.
**Detection formula:** `XLOOKUP(B2, Raw_Risk_Profiles!$A:$A, Raw_Risk_Profiles!$B:$B, "Not Found")`
**Findings:** **35 transactions** from customers with no risk profile (flag = "CRITICAL: No Risk Profile").
These transactions cannot be properly risk-scored for AML screening — a compliance gap.
**Remediation:** Enrich customer master for flagged Customer_IDs; apply default "High" risk rating pending review.

### Check 4: Expired / Pending KYC Status
**Issue:** Customers transacting with expired or pending KYC verification.
**Detection formula:** `IF(I2="Expired","WARN: KYC Expired",IF(I2="Pending","INFO: KYC Pending","OK"))`
**Findings:** **480 transactions** from customers with non-complete KYC status.
KYC-expired customers are flagged as "WARN" — transactions from these accounts should be reviewed before processing.
**Remediation:** Customer Operations to initiate KYC refresh; flag accounts for enhanced due diligence.

---

## Summary Table

| Check | Issue Found | Count | Severity | Action |
|---|---|---|---|---|
| Orphaned alerts | Alert with no matching transaction | 10 | High | Escalate to source system |
| Duplicate transactions | Same customer/date/amount | 5 | Medium | Dedup; retain earliest ID |
| Missing risk profiles | Customer not in risk master | 35 | High | Default to High risk; enrich master |
| Expired/Pending KYC | Customer KYC not current | 480 | Medium | Enhanced due diligence |

---

## Structuring Pattern Identified
During weekly trend analysis, **Week 6 (Feb 9–15)** showed an anomalous spike in Structuring alerts.
Investigation revealed **20 customers** each made 4–6 cash deposits of **$9,000–$9,999** within the same 7-day window —
a classic structuring pattern designed to stay below the $10,000 CTR reporting threshold.

**All 20 customers** already carry a High Risk Rating in the customer master.
Recommended action: File Suspicious Activity Reports (SARs) and escalate to AML investigations team.
