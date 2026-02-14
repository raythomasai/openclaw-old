# Systematic Edges in Prediction Markets
**Source:** QuantPedia (Dec 2025)
**Date Filed:** 2026-02-05
**URL:** https://quantpedia.com/systematic-edges-in-prediction-markets/

---

## Executive Summary

Prediction markets have systematic inefficiencies that create trading opportunities. Three main edges:

1. **Inter-exchange arbitrage** (Polymarket vs Kalshi) - 0.5-3% profits, exist for seconds-minutes
2. **Intra-exchange arbitrage** (mispriced contracts) - Buy all when sum < $1
3. **Longshot bias** - Retail overvalues underdogs, favorites underpriced

---

## 1. INTER-EXCHANGE ARBITRAGE ⭐⭐⭐⭐⭐

### The Strategy
Buy YES on one platform, NO on the other when prices diverge.

### How It Works
```
Example: Fed Rate Cut
- Polymarket YES: $0.45
- Kalshi NO: $0.52

Buy YES on Polymarket ($0.45) + Buy NO on Kalshi ($0.52) = $0.97
Guaranteed payout = $1.00
Profit = $0.03 (3%)
```

### Key Findings (from SSRN study)
- Polymarket generally LEADS Kalshi due to higher liquidity
- Arbitrage opportunities exist only for **seconds to minutes**
- Transaction costs significantly reduce profits
- Most profitable during last hours before market close

### Bot Implementation
```python
# Cross-platform arb check
def check_arbitrage(poly_price, kalshi_price):
    if poly_yes + kalshi_no < 0.97:  # After fees
        return True  # Execute arb
```

### Viability: HIGH
- Proven edge (SSRN research confirms)
- Easy to automate
- Low capital requirements for small profits

---

## 2. INTRA-EXCHANGE ARBITRAGE ⭐⭐⭐⭐

### The Strategy
Buy ALL contracts in a market when sum of prices < $1

### How It Works
```
Example: 4-candidate election
- Candidate A YES: $0.25
- Candidate B YES: $0.25
- Candidate C YES: $0.25
- Candidate D YES: $0.20
SUM = $0.95 (should equal $1.00)

Buy all for $0.95 → Guaranteed $1 payout regardless of winner
Profit = $0.05 (5.3%)
```

### Conditions for Opportunity
1. Sum of YES prices < $1.00
2. High liquidity markets
3. Before market closes

### Viability: MEDIUM
- Rare in liquid markets
- More common in election markets with many candidates
- The "Gabagool method" applies this principle

---

## 3. LONGSHOT BIAS ⭐⭐⭐⭐

### The Strategy
Bet on FAVORITES, not underdogs

### Why It Works
- Retail traders chase 10x payouts on longshots
- This overprices underdogs (> true probability)
- Underprices favorites (< true probability)

### Research Findings
- Football betting study: Favorites = -3.64% ROI, Longshots = -26.08% ROI
- "Lottery effect" in stocks/ETFs similar
- Professionals underinvest in "boring" favorites

### Bot Implementation
```python
# Longshot bias strategy
if price < 0.15:  # Underdog territory
    signal = "AVOID"
elif price > 0.80:  # Heavy favorite
    if confidence > 0.85:
        signal = "BUY"
```

### Viability: HIGH
- Behavioral bias is persistent
- Works across all markets (sports, politics, crypto)
- Compounding small edges over time

---

## 4. ADDITIONAL STRATEGIES

### Price Discovery Following
- Follow Polymarket (higher liquidity) for leading indicators
- Kalshi catches up with 30min-2hr lag
- Momentum strategy works on this lag

### Meta-Arbitrage
- Monitor Manifold Markets for consensus
- If Manifold says Polymarket 47%, Kalshi 34% → Kalshi might reprice

---

## IMPLEMENTATION PRIORITY

| Priority | Strategy | Effort | Edge | Frequency |
|----------|----------|--------|------|-----------|
| 1 | Cross-platform arb | Low | 0.5-3% | Seconds-minutes |
| 2 | Intra-market arb | Medium | 1-5% | Rare |
| 3 | Longshot bias | Low | 2-5% | Always |
| 4 | Momentum follow | Low | 1-2% | Events |

---

## KEY TAKEAWAYS

1. **Speed matters** - Arb opportunities close in seconds
2. **Fees kill profits** - Need >3% spread to be worth it
3. **Liquidity required** - Small accounts can't move markets
4. **Polymarket leads** - Use as signal, execute on Kalshi
5. **Favorites win** - Longshot bias is persistent

---

## REFERENCES

1. Price Discovery and Trading in Prediction Markets (SSRN, 2024)
2. Unravelling the Probabilistic Forest (Arxiv, 2025)
3. Election Arbitrage During 2024 U.S. Election (SSRN, 2024)
4. Biases in Football Betting Market (SSRN, 2017)
