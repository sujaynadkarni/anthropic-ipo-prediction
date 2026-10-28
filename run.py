"""Print the valuation. Usage: python run.py [--offline]"""

import sys

from valuation import inputs as I
from valuation import model as M
from valuation.peers import peer_multiples


def main(live: bool) -> None:
    multiples, source = peer_multiples(live)
    print(f"Peer EV / next-year revenue ({source})")
    for ticker, m in multiples.items():
        print(f"  {I.PEER_TICKERS[ticker]:<10} {m:5.1f}x")
    print(f"  Assumed for Anthropic: {I.MULTIPLE_LOW:.0f}-{I.MULTIPLE_HIGH:.0f}x\n")

    print(f"Fully diluted shares:  {I.FULLY_DILUTED_SHARES / 1e9:.1f}B")
    print(f"Broadcom lease debt:   ${M.broadcom_lease_debt():.0f}B")
    print(f"Net cash after leases: ${M.net_cash():.0f}B\n")

    print(f"{'Scenario':<16}{'Q/Q growth':>11}{'2027 revenue':>14}{'Fair value / share':>21}")
    for name, g in I.GROWTH_SCENARIOS.items():
        lo, hi = M.fair_value_range(g)
        print(f"{name:<16}{g:>10.1f}x{M.revenue_2027(g):>12.0f}B{f'${lo:.0f} - ${hi:.0f}':>21}")

    base = I.GROWTH_SCENARIOS["base"]
    lo, hi = M.fair_value_range(base)
    ipo_lo, ipo_hi = M.ipo_range(base)
    print(f"\nBase case fair value: ~${(lo + hi) / 2:.0f}/share  (range ${lo:.0f}-${hi:.0f})")
    print(f"Implied IPO range:    ${ipo_lo:.0f}-${ipo_hi:.0f}")
    print(f"Series H (May-Jun 2026): ${I.SERIES_H_PRICE_PER_COMMON:.2f}")


if __name__ == "__main__":
    main(live="--offline" not in sys.argv)
