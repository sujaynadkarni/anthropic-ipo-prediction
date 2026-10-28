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
python run.py            # live peer data from yfinance
python run.py --offline  # use the 2026-10-27 peer snapshot
```

No API keys or environment variables are required.

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

Why 1.3x as the base: 2.4x/quarter would put 2027 revenue at ~$3.7T, which is impossible. **Compute is the real limit.** Spreading each compute contract evenly over its term gives roughly $100B of compute available in 2027. At today's compute-to-revenue ratio (~48%), that supports ~$210B of revenue, which corresponds to **~1.4x a quarter (the ceiling)**. 1.2x is the stress case; 1.3x is the base.

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
| Financials, commitments, notes, share structure | [Anthropic S-1, SEC EDGAR](https://www.sec.gov/Archives/edgar/data/2130357/000162828026067168/anthropicpbc-sx1.htm) (filed 2026-10-26), read via browser and transcribed into `valuation/inputs.py` with section references |
| Peer EV and revenue estimates | [yfinance](https://github.com/ranaroussi/yfinance) (unofficial Yahoo Finance scraper; no key) |
| OpenAI valuation and revenue | Press reports, e.g. [CNBC](https://www.cnbc.com/2026/10/22/openai-funding-round-uae-investors.html), [Bloomberg](https://www.bloomberg.com/news/articles/2026-10-22/openai-shifts-value-to-1-25-trillion-as-funding-talks-finalize), [Sacra](https://sacra.com/c/openai/) (unaudited, numbers conflict) |
| xAI valuation | [CNBC](https://www.cnbc.com/2026/02/03/musk-xai-spacex-biggest-merger-ever.html) |

Note: scripted requests to SEC EDGAR require a `User-Agent` header with a contact email. This project doesn't fetch from EDGAR in code; if you add that, put your contact in an environment variable, never in the code.

## Tech stack
- **Python 3.9+**
- **yfinance** for live peer data (falls back to a hard-coded snapshot)
- No other dependencies

## Project layout

```
valuation/inputs.py   every number used, with its S-1 section or rationale
valuation/model.py    revenue projection, lease PV, price per share
valuation/peers.py    peer multiples (live or snapshot)
run.py                prints the full valuation
```

## Limitations
- The 2027 revenue forecast is a single constant growth rate, not a bottom-up model.
- Compute capacity in 2027 is a straight-line estimate across contracts that likely ramp up over time.
- The gross margin allocation isn't disclosed, so it isn't modeled; the revenue multiple stands in for it.
- The share count will change in the S-1/A; update `FULLY_DILUTED_SHARES` when it's published.
- Governance (founders' 50.1% voting control) isn't explicitly discounted.

## Next
Compare against the actual price range in the S-1/A, expected around the roadshow launch (reportedly the week of November 9, 2026).
