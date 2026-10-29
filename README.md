# Anthropic IPO Valuation

A learning project: estimating Anthropic's IPO price from its S-1, step by step, the way an equity analyst would. Built collaboratively with Claude Code on 2026-10-27, the day after the S-1 was filed.

> **Not investment advice.** This is an educational exercise built on our own assumptions. Note that the assistant used (Claude) is made by Anthropic, the company being valued. Read the framing with that conflict in mind.

## Result

| Scenario | Quarterly growth | 2027 revenue | Fair value / share |
|---|---|---|---|
| Stress | 1.2x | $101B | $60–90 |
| **Base** | **1.3x** | **$148B** | **$88–132 (~$110)** |
| Compute ceiling | 1.4x | $212B | $126–189 |

**Base-case IPO range: ~$93–99/share.** The latest private price (Series H, May–June 2026) was $58.90/share.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Collect data (optional: data/ is already committed)
SEC_USER_AGENT="Your Name you@example.com" python -m scrapers.edgar   # S-1 tables and facts
python -m scrapers.peers                                              # peer multiples

# 2. Run the model
python run.py

# 3. Check results still match
python -m unittest
```

No API keys are needed. SEC EDGAR asks every script to identify itself with a name and email in the `User-Agent` header; pass yours through the `SEC_USER_AGENT` environment variable. It is never written to disk.

## Data pipeline

```
SEC EDGAR (S-1 HTML) --scrapers/edgar.py--> data/s1/*.csv  --+
Yahoo Finance        --scrapers/peers.py--> data/peers.csv  --+--> valuation/ --> run.py --> data/outputs/scenarios.csv
Hand-curated, sourced -------------------> data/*.csv       --+
```

| File | Contents | How it's made |
|---|---|---|
| `data/s1/quarterly.csv` | Revenue and compute cost by quarter, Q1 2025–Q2 2026 | Parsed from the S-1 quarterly results table |
| `data/s1/income_statement.csv` | Annual and half-year expenses by type | Parsed from the summary financial table |
| `data/s1/opex_by_function.csv` | Cost of revenue, R&D, S&M, G&A (Note 8) | Parsed from the notes to the financial statements |
| `data/s1/commitments.csv` | Non-cancelable commitments by year | Parsed from the commitments table |
| `data/s1/facts.csv` | Cash, lease totals, share counts, Series H price, split ratio, etc. | Regex over the filing text; each row keeps the exact sentence it came from |
| `data/compute_contracts.csv` | Each compute deal: amount, term, estimated 2027 spend | Hand-curated from the MD&A; `scrapers/edgar.py` checks every quote appears verbatim in the filing |
| `data/peers.csv` | Peer EV, revenue estimates, multiples | `scrapers/peers.py` via yfinance |
| `data/private_rounds.csv` | OpenAI, xAI and Anthropic private valuations | Hand-curated from press reports, with source links (news sites are paywalled, so not scraped) |
| `data/outputs/scenarios.csv` | Model results by scenario | Written by `run.py` |

The original S-1 is committed at `data/raw/anthropic-s1.htm` (14 MB, public SEC filing), so `python -m scrapers.edgar` re-parses it without contacting SEC.

When the amended S-1 (S-1/A) is filed, re-run `scrapers/edgar.py --url <new filing URL> --force` and the model picks up the new numbers.

## How the analysis was done

The model is one formula:

```
price per share = (forward multiple × 2027 revenue + cash − lease debt) ÷ fully diluted shares
```

Each piece was decided in order:

### 1. Read the S-1
Pulled the S-1 from SEC EDGAR and read the sections that matter for pricing: financials, MD&A (compute, commitments, convertible notes), related-party transactions, capital structure and Note 8 (expenses by function). The price range and final share count are still blank in this first filing; they'll come in an S-1/A.

Key findings:
- Revenue went from $0.38B (Q1 2025) to **$11.56B (Q2 2026)**, growing 2.4x in the latest quarter.
- Gross margin is ~85% in H1 2026 as reported, but only ~45% if all compute is counted as a cost. How compute is split between serving customers and R&D isn't disclosed.
- **~$0.5T of compute commitments** (Broadcom, Google, Amazon, Microsoft, Nscale, Lambda), plus variable deals.
- Google, Amazon and Broadcom are suppliers, investors and (for Google) customers at once, with note facilities that settle in stock.
- The founders' LLC holds 50.1% of the votes; the Long-Term Benefit Trust elects a board majority.
- 5–7% of recent revenue came from customers violating the usage policy.
- 10-for-1 stock split on 2026-09-17; preferred stock converts 10:1.

### 2. Pick comparables
No public company looks like Anthropic. The closest competitor, OpenAI, is private, and Google and Microsoft are diversified. So we used:
- **Private rounds:** OpenAI's pending $1.25T round at ~$50–70B run rate (≈10–12x forward revenue). xAI was dropped: it was valued at ~500x its tiny revenue inside the SpaceX merger.
- **Public peers by trait:** Palantir (AI premium, ~38x), NVIDIA (AI growth at scale, ~8x), CoreWeave (compute-heavy, ~3x). Multiples are EV / next-fiscal-year revenue.

We picked **10–15x forward revenue**: between NVIDIA and Palantir, anchored on OpenAI, discounted a bit because private-round prices don't translate directly to public markets and because of the compute-commitment risk.

### 3. Forecast 2027 revenue
- Start from Q2 2026 ($11.56B).
- Cut Q3 2026 by **6%** once (usage-policy violators removed in Aug–Sep).
- Grow at a constant quarterly rate through Q4 2027 and sum the four 2027 quarters.

Why 1.3x as the base: 2.4x/quarter would put 2027 revenue at ~$3.7T, which is impossible. **Compute is the real limit.** Spreading each compute contract in `data/compute_contracts.csv` over its term gives about $103B of compute in 2027 (`model.compute_spend_2027`). At today's compute-to-revenue ratio (~48%), that supports ~$210B of revenue, which `model.compute_ceiling_growth` solves to **1.40x a quarter (the ceiling)**. 1.2x is the stress case; 1.3x is the base.

### 4. Adjust from enterprise value to equity value
- **Add cash:** $112.4B cash + $19.3B short-term investments (June 30, 2026).
- **Subtract Broadcom leases as debt:** $161.2B over 5 years, discounted at 9% with a 1-year start delay ≈ **$115B**. These are finance leases, which is debt in substance.
- **Cloud purchase deals are *not* subtracted.** They're operating costs of the revenue we're already valuing, so subtracting them would double-count. Their risk belongs in the bear case.

### 5. Divide by shares
- **16.9B fully diluted shares**, inferred from the Public Benefit Fund grant (846.8M shares = 5% of fully diluted, including Amazon's convertible notes).
- New shares sold for cash at a fair price (IPO shares, Google's $10B option, future Amazon/Google draws) don't dilute value per share, so they're ignored.
- Ignored as small: Broadcom notes converting at a 10% discount (≈ −$0.25/share). The Public Benefit Fund's +2% issuance per +50% price rise affects upside, not the IPO price.

### 6. IPO discount
Banks usually price 10–15% below expected trading value so the stock rises on day one. Applied to the base-case midpoint (~$110), that gives **~$93–99**.

## Sensitivity
Growth dominates everything. Going from 1.4x to 1.2x quarterly growth roughly halves the price. The multiple matters second; the balance-sheet adjustments barely move it (Broadcom leases ≈ −$7/share).

## Data sources

| Data | Source |
|---|---|
| Financials, commitments, notes, share structure | [Anthropic S-1, SEC EDGAR](https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm) (filed 2026-10-26), downloaded and parsed by `scrapers/edgar.py` |
| Peer EV and revenue estimates | [yfinance](https://github.com/ranaroussi/yfinance) (unofficial Yahoo Finance scraper; no key) |
| OpenAI valuation and revenue | Press reports, e.g. [CNBC](https://www.cnbc.com/2026/10/22/openai-funding-round-uae-investors.html), [Bloomberg](https://www.bloomberg.com/news/articles/2026-10-22/openai-shifts-value-to-1-25-trillion-as-funding-talks-finalize), [Sacra](https://sacra.com/c/openai/) (unaudited, numbers conflict) |
| xAI valuation | [CNBC](https://www.cnbc.com/2026/02/03/musk-xai-spacex-biggest-merger-ever.html) |

## Tech stack
- **Python 3.9+**
- **requests + BeautifulSoup** to download and parse the S-1 from SEC EDGAR
- **yfinance** for peer market data (no key)
- **unittest** to check the data and model reproduce the published results

## Project layout

```
scrapers/edgar.py     download the S-1 and extract tables and facts into data/s1/
scrapers/peers.py     fetch peer multiples into data/peers.csv
data/                 all inputs (scraped and hand-curated) and outputs, as CSV
valuation/inputs.py   loads data/ and holds the stated assumptions
valuation/model.py    revenue projection, compute ceiling, lease PV, price per share
run.py                prints the valuation and writes data/outputs/scenarios.csv
tests/                checks the pipeline reproduces the published numbers
docs/                 GitHub Pages write-up
```

## Limitations
- The 2027 revenue forecast is a single constant growth rate, not a bottom-up model.
- Compute capacity in 2027 is a straight-line estimate across contracts that likely ramp up over time.
- The gross margin allocation isn't disclosed, so it isn't modeled; the revenue multiple stands in for it.
- The share count is inferred from one sentence in the S-1; the S-1/A should give the real number.
- Compute contract end months and 2027 estimates for SpaceXAI, Broadcom and AMD are assumptions, noted in the CSV.
- The S-1 parser matches table labels and sentence wording; if an amendment rewords them, it stops with an error naming what it couldn't find.
- Governance (founders' 50.1% voting control) isn't explicitly discounted.

## Next
Compare against the actual price range in the S-1/A, expected around the roadshow launch (reportedly the week of November 9, 2026).

## Web page
A short newspaper-style write-up lives in `docs/` (`index.html` + `methodology.html`), served with GitHub Pages from the `/docs` folder on `main`.
