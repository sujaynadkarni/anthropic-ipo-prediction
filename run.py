"""Print the valuation and write data/outputs/scenarios.csv.

Usage: python run.py   (reads data/; refresh it with the scrapers first if needed)
"""

import csv

from valuation import inputs as I
from valuation import model as M

OUTPUT = I.DATA / "outputs" / "scenarios.csv"


def main() -> None:
    print(f"Latest reported quarter: {I.LAST_QUARTER}  revenue ${I.QUARTERLY_REVENUE[I.LAST_QUARTER]:.2f}B\n")

    print("Peer EV / next-year revenue (data/peers.csv)")
    for p in I.PEERS:
        print(f"  {p['name']:<10} {float(p['ev_to_next_fy_revenue']):5.1f}x  (fetched {p['fetched_on']})")
    print(f"  Assumed for Anthropic: {I.MULTIPLE_LOW:.0f}-{I.MULTIPLE_HIGH:.0f}x\n")

    spend = M.compute_spend_2027()
    print("Contracted compute in 2027 (data/compute_contracts.csv)")
    for name, v in spend.items():
        print(f"  {name:<22} ${v:5.1f}B")
    print(f"  Total ${sum(spend.values()):.0f}B at compute/revenue {M.compute_to_revenue_ratio():.0%}"
          f" -> ceiling {M.compute_ceiling_growth():.2f}x per quarter\n")

    print(f"Fully diluted shares:  {I.FULLY_DILUTED_SHARES / 1e9:.1f}B")
    print(f"Broadcom lease debt:   ${M.broadcom_lease_debt():.0f}B")
    print(f"Net cash after leases: ${M.net_cash():.0f}B\n")

    rows = []
    print(f"{'Scenario':<16}{'Q/Q growth':>11}{'2027 revenue':>14}{'Fair value / share':>21}")
    for name, g in I.GROWTH_SCENARIOS.items():
        lo, hi = M.fair_value_range(g)
        rev = M.revenue_2027(g)
        rows.append([name, g, round(rev, 1), round(lo, 2), round(hi, 2)])
        print(f"{name:<16}{g:>10.1f}x{rev:>12.0f}B{f'${lo:.0f} - ${hi:.0f}':>21}")

    base = I.GROWTH_SCENARIOS["base"]
    lo, hi = M.fair_value_range(base)
    ipo_lo, ipo_hi = M.ipo_range(base)
    print(f"\nBase case fair value: ~${(lo + hi) / 2:.0f}/share  (range ${lo:.0f}-${hi:.0f})")
    print(f"Implied IPO range:    ${ipo_lo:.0f}-${ipo_hi:.0f}")
    print(f"Series H (May-Jun 2026): ${I.SERIES_H_PRICE_PER_COMMON:.2f}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "quarterly_growth", "revenue_2027_bn", "price_low", "price_high"])
        w.writerows(rows)
    print(f"\nWrote {OUTPUT.relative_to(I.DATA.parent)}")


if __name__ == "__main__":
    main()
