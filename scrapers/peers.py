"""Fetch peer valuation data from Yahoo Finance via yfinance (no API key).

Usage: python -m scrapers.peers
Writes data/peers.csv, which the model reads. yfinance is unofficial and can
break when Yahoo changes its pages; the committed CSV is the fallback.
"""

import csv
from datetime import date
from pathlib import Path

import yfinance as yf

PEERS = {
    "PLTR": ("Palantir", "AI premium"),
    "NVDA": ("NVIDIA", "AI growth at scale"),
    "CRWV": ("CoreWeave", "Compute-heavy, high debt"),
}
OUT = Path(__file__).resolve().parent.parent / "data" / "peers.csv"


def main() -> None:
    rows = []
    for ticker, (name, trait) in PEERS.items():
        t = yf.Ticker(ticker)
        info = t.info
        ev = info["enterpriseValue"] / 1e9
        next_fy = t.revenue_estimate.loc["+1y", "avg"] / 1e9
        rows.append([
            ticker, name, trait, round(ev, 1), round(info["totalRevenue"] / 1e9, 2),
            round(next_fy, 2), round(info.get("revenueGrowth") or 0, 3),
            round(info.get("grossMargins") or 0, 3), round(ev / next_fy, 1), date.today().isoformat(),
        ])
        print(f"  {name:<10} EV ${ev:,.0f}B  next-FY revenue ${next_fy:,.1f}B  -> {ev / next_fy:.1f}x")

    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "name", "trait", "ev_bn", "ttm_revenue_bn", "next_fy_revenue_bn",
                    "revenue_growth", "gross_margin", "ev_to_next_fy_revenue", "fetched_on"])
        w.writerows(rows)
    print(f"Wrote {OUT.name}")


if __name__ == "__main__":
    main()
