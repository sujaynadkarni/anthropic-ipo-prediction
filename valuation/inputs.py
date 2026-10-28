"""Every number the model uses, with where it came from.

S-1 = Anthropic, PBC Form S-1 filed 2026-10-26
https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm
Figures in $ billions unless noted.
"""

# --- From the S-1 -----------------------------------------------------------

# MD&A, quarterly results table ("Three Months Ended")
QUARTERLY_REVENUE = {
    "Q1 2025": 0.376,
    "Q2 2025": 0.787,
    "Q3 2025": 1.382,
    "Q4 2025": 2.040,
    "Q1 2026": 4.731,
    "Q2 2026": 11.555,
}
LAST_QUARTER = "Q2 2026"

# MD&A, "Components of Results of Operations": 5-7% of 9M 2026 revenue came from
# customers violating usage policy; enforcement ramped Aug-Sep 2026.
USAGE_VIOLATION_HAIRCUT = 0.06  # midpoint, applied once to Q3 2026

# MD&A, "Quantitative and Qualitative Disclosures about Market Risk" (June 30, 2026)
CASH = 112.4
SHORT_TERM_INVESTMENTS = 19.3

# MD&A, "Contractual Obligations - Infrastructure Equipment Leases":
# Broadcom 5-year finance leases, ~$161.2B rent excluding interest.
BROADCOM_LEASE_TOTAL = 161.2
BROADCOM_LEASE_YEARS = 5
# Discount rate: interest on the Broadcom notes that can fund this rent (MD&A, "Convertible Notes - Broadcom").
BROADCOM_DISCOUNT_RATE = 0.09
# Most capacity comes online starting 2027, so payments start ~1 year out.
BROADCOM_START_DELAY_YEARS = 1

# Prospectus Summary: 846,840,960 Class N shares to the Public Benefit Fund =
# "5% of our fully diluted shares as of June 30, 2026 (assuming full conversion of the Amazon Notes)".
# Share counts are post 10-for-1 split (2026-09-17).
PUBLIC_BENEFIT_SHARES = 846_840_960
FULLY_DILUTED_SHARES = PUBLIC_BENEFIT_SHARES / 0.05

# Related-party section: Series H-1 at $589.0095/preferred share; preferred converts 10:1 (Note 1, "Stock Split").
SERIES_H_PRICE_PER_COMMON = 589.0095 / 10

# --- Our assumptions ----------------------------------------------------------

# Quarter-over-quarter revenue growth from Q3 2026 through Q4 2027.
# 1.4x ~ what contracted compute can support in 2027; 1.2x = stress case.
GROWTH_SCENARIOS = {"stress": 1.2, "base": 1.3, "compute ceiling": 1.4}

# EV / next-year revenue. Anchors: NVIDIA ~8x, Palantir ~38x, OpenAI pending round ~10-12x forward.
MULTIPLE_LOW, MULTIPLE_HIGH = 10.0, 15.0

# Banks typically price IPOs 10-15% below expected trading value.
IPO_DISCOUNT_LOW, IPO_DISCOUNT_HIGH = 0.10, 0.15

PEER_TICKERS = {"PLTR": "Palantir", "NVDA": "NVIDIA", "CRWV": "CoreWeave"}
