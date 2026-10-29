"""Download Anthropic's S-1 from SEC EDGAR and extract what the model uses.

EDGAR requires every scripted request to identify itself with a User-Agent such as
"Jane Doe jane@example.com". Set it in the SEC_USER_AGENT environment variable;
it is only sent to sec.gov and never written to disk.

Usage:
    SEC_USER_AGENT="Your Name you@example.com" python -m scrapers.edgar
    python -m scrapers.edgar --url <S-1/A url>   # re-run on an amendment

Writes:
    data/raw/anthropic-s1.htm          cached filing (git-ignored, ~14 MB)
    data/s1/quarterly.csv              revenue and compute by quarter
    data/s1/income_statement.csv       annual + half-year expenses by nature
    data/s1/opex_by_function.csv       Note 8: cost of revenue, R&D, S&M, G&A
    data/s1/commitments.csv            non-cancelable commitments by year
    data/s1/facts.csv                  single numbers pulled from the text, with the quote
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

S1_URL = (
    "https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm"
)
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "anthropic-s1.htm"
OUT = ROOT / "data" / "s1"
CONTRACTS = ROOT / "data" / "compute_contracts.csv"

QUARTER_OF_MONTH = {"March": "Q1", "June": "Q2", "September": "Q3", "December": "Q4"}
PERIOD_COLUMNS = ["FY2023", "FY2024", "FY2025", "H1 2025", "H1 2026"]
FILLER_CELLS = {"", "$", ")", "%"}


# --- download ------------------------------------------------------------------

def download(url: str, force: bool = False) -> bytes:
    if RAW.exists() and not force:
        return RAW.read_bytes()
    user_agent = os.environ.get("SEC_USER_AGENT")
    if not user_agent:
        sys.exit('Set SEC_USER_AGENT, e.g. SEC_USER_AGENT="Jane Doe jane@example.com"')
    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=120)
    resp.raise_for_status()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(resp.content)
    return resp.content


# --- table helpers ---------------------------------------------------------------

def table_rows(table) -> list:
    """Each <tr> as a list of non-empty cell texts (EDGAR splits '$' and ')' into own cells)."""
    rows = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True).replace("\xa0", " ") for c in tr.find_all(["td", "th"])]
        cells = [re.sub(r"\s+", " ", c) for c in cells if c.strip() not in FILLER_CELLS]
        if cells:
            rows.append(cells)
    return rows


def find_table(soup, *needles: str):
    for table in soup.find_all("table"):
        text = re.sub(r"\s+", " ", table.get_text(" ").replace("\xa0", " "))
        if all(n in text for n in needles):
            return table
    raise LookupError(f"No table containing {needles}")


def parse_number(cell: str) -> float:
    s = cell.replace("$", "").replace(",", "").strip()
    if s in {"—", "-", "–"}:
        return 0.0
    negative = s.startswith("(")
    value = float(s.strip("()"))
    return -value if negative else value


def row_values(rows: list, label: str, n: int) -> list:
    for row in rows:
        if re.sub(r"\(\d\)$", "", row[0]).strip() == label:
            values = [parse_number(c) for c in row[1:]]
            if len(values) != n:
                raise ValueError(f"{label!r}: expected {n} values, got {values}")
            return values
    raise LookupError(f"Row {label!r} not found")


def write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# --- extractors --------------------------------------------------------------------

def extract_quarterly(soup) -> list:
    rows = table_rows(find_table(soup, "Three Months Ended", "Revenue", "Compute and infrastructure", "(in millions)"))
    header = next(r for r in rows if len(re.findall(r"(March|June|September|December) \d+", " ".join(r))) >= 4)
    quarters = [
        f"{QUARTER_OF_MONTH[m]} {y}"
        for m, y in re.findall(r"(March|June|September|December) \d+,\s*(\d{4})", " ".join(header))
    ]
    revenue = row_values(rows, "Revenue", len(quarters))
    compute = row_values(rows, "Compute and infrastructure", len(quarters))
    out = [[q, r, c] for q, r, c in zip(quarters, revenue, compute)]
    write_csv(OUT / "quarterly.csv", ["quarter", "revenue_m", "compute_and_infrastructure_m"], out)
    return out


def extract_period_table(soup, needles: tuple, labels: list, filename: str) -> list:
    rows = table_rows(find_table(soup, *needles))
    out = [[label] + row_values(rows, label, len(PERIOD_COLUMNS)) for label in labels]
    write_csv(OUT / filename, ["line_item_m"] + PERIOD_COLUMNS, out)
    return out


def extract_commitments(soup) -> list:
    rows = table_rows(find_table(soup, "Total non-cancelable contractual commitments"))
    out = [[r[0], parse_number(r[1])] for r in rows if len(r) == 2 and re.match(r"\d{4}|Thereafter|Total", r[0])]
    write_csv(OUT / "commitments.csv", ["year", "amount_m"], out)
    return out


# Each fact: regex with numeric groups, unit, and how to turn the groups into one value.
FACTS = {
    "usage_violation_revenue_pct_low": (r"approximately (\d+)% to (\d+)% of our revenue for the nine months", "%", lambda g: g[0]),
    "usage_violation_revenue_pct_high": (r"approximately (\d+)% to (\d+)% of our revenue for the nine months", "%", lambda g: g[1]),
    "top5_customer_revenue_pct": (r"top five customers represented approximately (\d+)% of our revenue", "%", lambda g: g[0]),
    "cash_bn": (r"we had \$([\d.]+) billion of cash and cash equivalents", "$B", lambda g: g[0]),
    "short_term_investments_bn": (r"cash and cash equivalents and \$([\d.]+) billion of short-term investments", "$B", lambda g: g[0]),
    # All Broadcom leases; a separate sentence gives $125.2B for the 2026 lease alone.
    "broadcom_lease_rent_bn": (r"rent payments over the life of these leases are equal to an aggregate of approximately \$([\d.]+) billion excluding interest", "$B", lambda g: g[0]),
    "broadcom_2026_lease_rent_bn": (r"2026 Lease Arrangement, the rent payments over the five-year equipment lease are equal to an aggregate of approximately \$([\d.]+) billion", "$B", lambda g: g[0]),
    "public_benefit_fund_shares": (r"contributed ([\d,]+) shares of our Class N common stock, representing 5% of our fully diluted shares", "shares", lambda g: g[0]),
    "series_h_price_per_preferred": (r"Series H-1 redeemable convertible preferred stock at a purchase price of \$([\d.]+) per share", "$", lambda g: g[0]),
    "preferred_conversion_ratio": (r"conversion ratio for all series of redeemable convertible preferred stock was (\d+):1", "x", lambda g: g[0]),
    "stock_split_ratio": (r"effected a (\d+)-for-1 stock split", "x", lambda g: g[0]),
}


def extract_facts(text: str) -> list:
    out = []
    for name, (pattern, unit, pick) in FACTS.items():
        m = re.search(pattern, text)
        if not m:
            raise LookupError(f"Fact {name!r} not found; the filing wording may have changed")
        value = parse_number(pick(m.groups()))
        out.append([name, value, unit, m.group(0)])
    write_csv(OUT / "facts.csv", ["name", "value", "unit", "s1_quote"], out)
    return out


def verify_contract_quotes(text: str) -> bool:
    """Every hand-curated compute contract must quote the filing verbatim."""
    ok = True
    with CONTRACTS.open() as f:
        for row in csv.DictReader(f):
            found = row["s1_quote"] in text
            ok &= found
            print(f"  {'ok ' if found else 'MISSING'} {row['counterparty']}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=S1_URL)
    parser.add_argument("--force", action="store_true", help="re-download even if cached")
    args = parser.parse_args()

    soup = BeautifulSoup(download(args.url, args.force), "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ").replace("\xa0", " "))
    # get_text(" ") splits inline tags, leaving "$ 44.9", "5 %" and "10 : 1"; rejoin them.
    text = re.sub(r"\$ (?=\d)", "$", text)
    text = re.sub(r"(\d) %", r"\1%", text)
    text = re.sub(r"(\d) : (\d)", r"\1:\2", text)

    quarterly = extract_quarterly(soup)
    extract_period_table(
        soup,
        ("Compute and infrastructure", "Operating loss", "Six Months Ended"),
        ["Revenue", "Compute and infrastructure", "Personnel", "Sales, marketing, and partnerships",
         "Other operating and administrative", "Total operating expenses", "Operating loss"],
        "income_statement.csv",
    )
    extract_period_table(
        soup,
        ("Cost of revenue", "Research and development", "Total operating expenses"),
        ["Cost of revenue", "Research and development", "Sales and marketing",
         "General and administrative", "Total operating expenses"],
        "opex_by_function.csv",
    )
    extract_commitments(soup)
    facts = extract_facts(text)

    print(f"Quarters: {quarterly[0][0]} to {quarterly[-1][0]} (latest revenue ${quarterly[-1][1]:,.0f}M)")
    print(f"Facts: {len(facts)} extracted")
    print("Compute contract quotes:")
    if not verify_contract_quotes(text):
        sys.exit("Some compute contract quotes were not found in the filing")
    print(f"Wrote {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
