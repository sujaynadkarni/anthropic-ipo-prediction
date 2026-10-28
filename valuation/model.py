"""Forward revenue -> enterprise value -> price per share."""

from . import inputs as I

PROJECTED_QUARTERS = ["Q3 2026", "Q4 2026", "Q1 2027", "Q2 2027", "Q3 2027", "Q4 2027"]


def project_quarters(growth: float, haircut: float = I.USAGE_VIOLATION_HAIRCUT) -> dict:
    """Grow from the last reported quarter; the usage-violation cut hits Q3 2026 once."""
    rev = I.QUARTERLY_REVENUE[I.LAST_QUARTER]
    out = {}
    for i, q in enumerate(PROJECTED_QUARTERS):
        rev *= growth
        if i == 0:
            rev *= 1 - haircut
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


def fair_value_range(growth: float) -> tuple[float, float]:
    return price_per_share(growth, I.MULTIPLE_LOW), price_per_share(growth, I.MULTIPLE_HIGH)


def ipo_range(growth: float) -> tuple[float, float]:
    """Apply the IPO discount to the midpoint fair value."""
    mid = sum(fair_value_range(growth)) / 2
    return mid * (1 - I.IPO_DISCOUNT_HIGH), mid * (1 - I.IPO_DISCOUNT_LOW)
