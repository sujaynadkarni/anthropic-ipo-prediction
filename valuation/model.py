"""Forward revenue -> enterprise value -> price per share."""

from datetime import date

from . import inputs as I

FORECAST_END = "Q4 2027"
# Usage-policy enforcement ramped in Aug-Sep 2026, so the cut lands in Q3 2026 (if it isn't reported yet).
HAIRCUT_QUARTER = "Q3 2026"


def _next_quarter(q: str) -> str:
    n, year = int(q[1]), int(q[3:])
    return f"Q{n % 4 + 1} {year + (n == 4)}"


def project_quarters(growth: float, haircut: float = I.USAGE_VIOLATION_HAIRCUT) -> dict:
    """Grow from the last reported quarter through Q4 2027."""
    rev, q, out = I.QUARTERLY_REVENUE[I.LAST_QUARTER], I.LAST_QUARTER, {}
    while q != FORECAST_END:
        q = _next_quarter(q)
        rev *= growth * (1 - haircut if q == HAIRCUT_QUARTER else 1)
        out[q] = rev
    return out


def revenue_2027(growth: float) -> float:
    quarters = project_quarters(growth)
    return sum(v for q, v in quarters.items() if q.endswith("2027"))


def broadcom_lease_debt() -> float:
    """Present value of the Broadcom finance leases, treated as debt."""
    annual = I.BROADCOM_LEASE_TOTAL / I.BROADCOM_LEASE_YEARS
    r = I.BROADCOM_DISCOUNT_RATE
    annuity = annual * (1 - (1 + r) ** -I.BROADCOM_LEASE_YEARS) / r
    return annuity / (1 + r) ** I.BROADCOM_START_DELAY_YEARS


def net_cash() -> float:
    return I.CASH + I.SHORT_TERM_INVESTMENTS - broadcom_lease_debt()


def price_per_share(growth: float, multiple: float) -> float:
    enterprise_value = multiple * revenue_2027(growth)
    equity_value = enterprise_value + net_cash()
    return equity_value * 1e9 / I.FULLY_DILUTED_SHARES


def fair_value_range(growth: float) -> tuple:
    return price_per_share(growth, I.MULTIPLE_LOW), price_per_share(growth, I.MULTIPLE_HIGH)


def ipo_range(growth: float) -> tuple:
    """Apply the IPO discount to the midpoint fair value."""
    mid = sum(fair_value_range(growth)) / 2
    return mid * (1 - I.IPO_DISCOUNT_HIGH), mid * (1 - I.IPO_DISCOUNT_LOW)


# --- Compute capacity check ---------------------------------------------------------

def _month(ym: str) -> date:
    y, m = ym.split("-")
    return date(int(y), int(m), 1)


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def compute_spend_2027() -> dict:
    """Approximate 2027 compute spend per contract: straight-line over the term unless overridden."""
    out = {}
    for c in I.COMPUTE_CONTRACTS:
        if c["method"] == "override":
            out[c["counterparty"]] = float(c["est_2027_bn"])
            continue
        start, end = _month(c["start"]), _month(c["end"])
        overlap = max(0, _months_between(max(start, date(2027, 1, 1)), min(end, date(2028, 1, 1))))
        out[c["counterparty"]] = float(c["total_bn"]) * overlap / _months_between(start, end)
    return out


def compute_to_revenue_ratio() -> float:
    q = I.LAST_QUARTER
    return I.QUARTERLY_COMPUTE[q] / I.QUARTERLY_REVENUE[q]


def compute_ceiling_growth() -> float:
    """Quarterly growth at which 2027 revenue uses up all contracted 2027 compute at today's ratio."""
    target = sum(compute_spend_2027().values()) / compute_to_revenue_ratio()
    lo, hi = 1.0, 3.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if revenue_2027(mid) < target else (lo, mid)
    return lo
