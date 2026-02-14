# Alpaca Trading - Lessons Learned & New Approach

## What Went Wrong

### Starting Position
- Portfolio: ~$462 (February 2, 2026)
- Goal: 1% daily returns

### What Actually Happened

| Metric | Target | Actual |
|--------|--------|--------|
| Daily Return | +1% | -0.5% avg |
| Win Rate | >60% | ~40% |
| Final Portfolio | Growing | $444.59 (-$17, -3.8%) |

### Specific Failures

1. **False Breakouts**
   - Bought into momentum breakouts that immediately reversed
   - Tight stops (1%) got triggered, then price recovered
   - Lost money on 60%+ of signals

2. **Over-Trading**
   - Generated signals every 30 seconds during market hours
   - Many signals were noise, not real opportunities
   - Transaction costs (even commission-free, there's bid-ask spread)

3. **No Edge**
   - Momentum strategies work in trending markets
   - Recent market was choppy - perfect environment to get whipsawed
   - Didn't adapt strategy to market conditions

4. **Position Sizing**
   - Too fragmented (5+ small positions)
   - Didn't concentrate when confident
   - Didn't scale out of winners

5. **Risk Management**
   - Daily loss limit worked but was too tight
   - Got stopped out multiple days in a row
   - "Halt trading" mode meant missing recovery days

---

## New Approach: Paper Trading First

### Phase 1: Paper Trading (Week 1-2)
- Test strategies with fake money ($10,000)
- Only trade when strategy has demonstrated edge
- Document every trade and outcome

### Phase 2: Validation (Week 2-3)
- Need 50+ trades with >55% win rate
- Need >2% monthly return
- Need <5% max drawdown

### Phase 3: Small Live Deployment (Week 3-4)
- Start with $500 (half of current portfolio)
- Apply validated strategies
- Scale up slowly

---

## Strategy Testing Results

### Backtest (Synthetic Data)

| Strategy | Return | Win Rate | Max Drawdown | Verdict |
|---------|--------|----------|--------------|---------|
| Momentum | +1.10% | 55.6% | 2.52% | ✅ Paper test |
| Mean Reversion | 0.0% | 0% | 0% | ❌ Needs work |

### Next Steps
1. Test momentum strategy with real historical data
2. Try different parameters
3. Add new strategies (RSI divergence, trend continuation)

---

## New Rules

### Before Any Trade
- [ ] Strategy backtested with 100+ trades
- [ ] Current market conditions match strategy's edge
- [ ] Position size calculated (1-2% risk max)
- [ ] Stop loss and target defined

### Daily Rules
- [ ] Maximum 3 trades per day
- [ ] Stop if 2 consecutive losses
- [ ] Review and log every trade

### Weekly Review
- [ ] Calculate win rate
- [ ] Identify what worked/didn't
- [ ] Adjust parameters if needed

---

## Current Portfolio Status

| Metric | Value |
|--------|-------|
| Cash | $444.59 |
| Positions | 0 (all closed) |
| Mode | PAUSED |

**Plan:** Paper trade for 2 weeks, then gradually resume with proven strategies.

---

## Questions to Answer Before Resuming

1. What's the actual edge of momentum strategies?
2. What's the win rate of buy-the-dip vs buy-the-breakout?
3. What's the best stop loss distance?
4. Should we trade only certain hours?

These can ONLY be answered through systematic testing.
