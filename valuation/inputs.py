"""Model inputs: facts loaded from data/ (produced by scrapers/), plus our stated assumptions.

Figures in $ billions unless noted.
"""

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def _read(path: Path) -> list:
    with path.open() as f:
        return list(csv.DictReader(f))


# --- From the S-1 (data/s1/, written by scrapers/edgar.py) ----------------------

_quarterly = _read(DATA / "s1" / "quarterly.csv")
QUARTERLY_REVENUE = {r["quarter"]: float(r["revenue_m"]) / 1000 for r in _quarterly}
QUARTERLY_COMPUTE = {r["quarter"]: float(r["compute_and_infrastructure_m"]) / 1000 for r in _quarterly}
LAST_QUARTER = _quarterly[-1]["quarter"]

FACTS = {r["name"]: float(r["value"]) for r in _read(DATA / "s1" / "facts.csv")}

# Midpoint of the 5-7% of revenue from usage-policy violators; applied once to the next quarter.
USAGE_VIOLATION_HAIRCUT = (FACTS["usage_violation_revenue_pct_low"] + FACTS["usage_violation_revenue_pct_high"]) / 200

CASH = FACTS["cash_bn"]
SHORT_TERM_INVESTMENTS = FACTS["short_term_investments_bn"]

BROADCOM_LEASE_TOTAL = FACTS["broadcom_lease_rent_bn"]
BROADCOM_LEASE_YEARS = 5  # "five-year master equipment leases with Broadcom"

# The Public Benefit Fund grant is described as 5% of fully diluted shares (incl. Amazon notes).
FULLY_DILUTED_SHARES = FACTS["public_benefit_fund_shares"] / 0.05

SERIES_H_PRICE_PER_COMMON = FACTS["series_h_price_per_preferred"] / FACTS["preferred_conversion_ratio"]

# --- Curated data (data/*.csv, each row with its source) -------------------------

COMPUTE_CONTRACTS = _read(DATA / "compute_contracts.csv")
PEERS = _read(DATA / "peers.csv")
PRIVATE_ROUNDS = _read(DATA / "private_rounds.csv")

# --- Our assumptions ----------------------------------------------------------------

# Interest rate on the Broadcom notes that can fund this rent; used to discount the leases.
BROADCOM_DISCOUNT_RATE = 0.09
# Most leased capacity comes online starting 2027, so payments start ~1 year out.
BROADCOM_START_DELAY_YEARS = 1

# Quarter-over-quarter revenue growth from Q3 2026 through Q4 2027.
# The compute ceiling is checked against data/compute_contracts.csv in model.compute_ceiling_growth().
GROWTH_SCENARIOS = {"stress": 1.2, "base": 1.3, "compute ceiling": 1.4}

# EV / next-year revenue, chosen between NVIDIA and Palantir and anchored on OpenAI's pending round.
MULTIPLE_LOW, MULTIPLE_HIGH = 10.0, 15.0

# Banks typically price IPOs 10-15% below expected trading value.
IPO_DISCOUNT_LOW, IPO_DISCOUNT_HIGH = 0.10, 0.15
