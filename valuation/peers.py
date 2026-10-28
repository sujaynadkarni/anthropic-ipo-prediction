"""Peer EV / next-year revenue from yfinance (no API key needed).

yfinance scrapes Yahoo Finance and is unofficial; if it fails we fall back to the
snapshot we pulled on 2026-10-27.
"""

from . import inputs as I

SNAPSHOT_2026_10_27 = {
    # ticker: (enterprise value $B, next-fiscal-year revenue estimate $B)
    "PLTR": (468.0, 12.4),
    "NVDA": (5229.0, 692.2),
    "CRWV": (79.0, 26.5),
}


def fetch_live() -> dict:
    import yfinance as yf

    out = {}
    for ticker in I.PEER_TICKERS:
        t = yf.Ticker(ticker)
        ev = t.info["enterpriseValue"] / 1e9
        next_year = t.revenue_estimate.loc["+1y", "avg"] / 1e9
        out[ticker] = (ev, next_year)
    return out


def peer_multiples(live: bool = True) -> tuple[dict, str]:
    data, source = SNAPSHOT_2026_10_27, "snapshot 2026-10-27"
    if live:
        try:
            data, source = fetch_live(), "yfinance (live)"
        except Exception as e:  # network down, Yahoo changed its page, etc.
            source = f"snapshot 2026-10-27 (live fetch failed: {type(e).__name__})"
    return {t: ev / rev for t, (ev, rev) in data.items()}, source
