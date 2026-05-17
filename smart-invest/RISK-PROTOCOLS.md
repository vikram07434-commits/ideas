# RISK PROTOCOLS — THE BIBLE

> This document is the absolute authority for Smart Invest.
> No code, no strategy, no trade can violate anything written here.
> If a situation is not covered, the default is: DO NOTHING.

---

## PREAMBLE

This system manages real money belonging to a person with zero investment experience.
The system's PRIMARY job is to NOT LOSE MONEY.
The system's SECONDARY job is to grow money.
These priorities are never reversed.

---

## CHAPTER 1: CAPITAL RULES

### 1.1 Allocation Limits
- Total investable capital must be defined ONCE and locked
- System CANNOT access funds beyond this allocation
- Emergency fund (6 months expenses) is NEVER part of investable capital
- Investment capital = money you can lose entirely without affecting life

### 1.2 Position Sizing
- Single position: MAX 5% of total portfolio
- Single asset class: MAX 40% of total portfolio
- Single geography: MAX 60% of total portfolio
- Single strategy: MAX 50% of total portfolio
- Cash reserve: ALWAYS maintain minimum 10% in liquid cash

### 1.3 Loss Limits (Circuit Breakers)
- Single trade loss: MAX 1% of portfolio → auto-close position
- Daily loss: MAX 2% of portfolio → halt all trading for 24h
- Weekly loss: MAX 5% of portfolio → halt all trading for 7 days
- Monthly loss: MAX 8% of portfolio → halt, full strategy review
- Total drawdown: MAX 15% from peak → KILL SWITCH, stop everything

### 1.4 What Happens When Kill Switch Triggers
1. All open positions are closed at market price
2. All pending orders are cancelled
3. System enters "LOCKED" state
4. Alert sent to all channels (Telegram, Email, SMS)
5. System CANNOT be restarted without manual intervention
6. Mandatory 30-day review period before restart
7. Capital reduction: restart with 50% of previous allocation

---

## CHAPTER 2: STRATEGY RULES

### 2.1 Strategy Approval Process
No strategy can be deployed without passing ALL of the following:

```
[  ] 10-year historical backtest (minimum)
[  ] 3-year out-of-sample test
[  ] Stress test: 2008 financial crisis
[  ] Stress test: 2020 COVID crash
[  ] Stress test: 2022 crypto winter
[  ] Stress test: Black Monday (1987)
[  ] Monte Carlo simulation (10,000 runs, 95% profitable)
[  ] Sharpe ratio > 1.0 (after fees and slippage)
[  ] Maximum drawdown < 20% in worst scenario
[  ] 6-month paper trading with live data
[  ] Paper results within 20% of backtest results
[  ] Independent verification (different codebase/tool)
[  ] Fee model includes ALL costs (brokerage, STT, GST, stamps, SEBI charges)
[  ] Tax model includes short-term and long-term capital gains
```

### 2.2 Strategy Monitoring (Live)
- Every strategy has a "health score" (0-100)
- Score drops below 60 → reduce position size by 50%
- Score drops below 40 → halt strategy, paper mode only
- Score drops below 20 → disable strategy permanently
- Score calculation: win rate + risk-adjusted returns + drawdown recovery

### 2.3 Strategy Retirement
- Any strategy that underperforms buy-and-hold for 6 consecutive months → retire
- Any strategy with > 3 consecutive losing months → mandatory review
- Any strategy that hits max drawdown even once in live → retired permanently

---

## CHAPTER 3: EXECUTION RULES

### 3.1 Order Placement
- NEVER place market orders (slippage risk) — always limit orders
- Order validity: DAY only — no GTC (Good Till Cancelled)
- Maximum order size: coded limit, cannot be changed without code review
- All orders logged BEFORE submission with: reason, expected outcome, risk
- Failed orders: retry MAX 3 times, then alert and halt

### 3.2 Timing Rules
- No trading in first 15 minutes of market open (volatility)
- No trading in last 15 minutes of market close (manipulation risk)
- No trading during major news events (scheduled via calendar)
- Crypto: avoid trading during extreme volume spikes (> 5x average)

### 3.3 Execution Verification
- After every trade: verify fill price vs expected price
- Slippage > 0.5%: alert and log as incident
- Slippage > 1%: halt strategy for review
- Position mismatch between system and broker: EMERGENCY HALT

---

## CHAPTER 4: SECURITY RULES

### 4.1 Credentials
- All API keys stored in encrypted vault (AES-256 minimum)
- Master password: 32+ characters, stored nowhere digitally
- API keys rotated every 30 days automatically
- Separate API keys for: read-only data, paper trading, live trading
- Live trading key: restricted to specific IP addresses only

### 4.2 Network
- All connections: TLS 1.3 minimum
- Certificate pinning for broker APIs
- VPN for all trading operations
- No trading from public WiFi — EVER
- DNS-over-HTTPS to prevent DNS poisoning

### 4.3 System Access
- System runs on dedicated machine/VPS — nothing else runs there
- OS hardened: no unnecessary services, auto-security-updates
- Firewall: allow only specific IPs and ports
- SSH key-only access (no password authentication)
- Failed login attempts: 3 strikes → lockout + alert

### 4.4 Code Security
- No third-party packages without security audit
- Dependency scanning on every update
- No dynamic code execution (eval, exec)
- Input validation on ALL external data
- SQL injection protection (parameterized queries only)

---

## CHAPTER 5: MONITORING & ALERTING

### 5.1 System Health Checks (Every 60 seconds)
- [ ] Market data feed alive?
- [ ] Broker API responsive?
- [ ] Database write successful?
- [ ] Portfolio value calculated?
- [ ] All positions accounted for?
- [ ] No orphaned orders?
- [ ] Memory/CPU within limits?
- [ ] Disk space sufficient?

### 5.2 Alert Priority Levels

| Level | Meaning | Response Time | Channel |
|-------|---------|---------------|---------|
| P0 - CRITICAL | Money at risk NOW | Immediate auto-action | Telegram + SMS + Email + Kill Switch |
| P1 - HIGH | System degraded | Within 5 minutes | Telegram + Email |
| P2 - MEDIUM | Anomaly detected | Within 1 hour | Telegram |
| P3 - LOW | Informational | Daily digest | Email |

### 5.3 P0 (Critical) Events — Auto Kill Switch
- Unauthorized login attempt on broker account
- Position value drops > 5% in < 1 minute
- Broker API returns unexpected responses
- System clock drift > 5 seconds
- Database corruption detected
- Network connectivity lost for > 2 minutes

---

## CHAPTER 6: DATA INTEGRITY

### 6.1 Market Data
- Minimum 2 independent data sources for price verification
- Price discrepancy > 1% between sources → halt, use neither
- Historical data: only from audited sources (exchange official feeds)
- No "free" data for backtesting — pay for quality or go without
- All data timestamped in UTC, stored with source metadata

### 6.2 Portfolio Data
- Single source of truth: the BROKER's position report
- System's internal state must reconcile with broker every 5 minutes
- Discrepancy found → HALT trading → alert → manual resolution
- Backup: daily portfolio snapshot to encrypted off-site storage

### 6.3 Audit Trail (Immutable)
Every event recorded with:
- Timestamp (UTC, millisecond precision)
- Event type (trade, alert, system, config change)
- Actor (system, user, scheduler)
- Before state
- After state
- Reason/trigger
- Outcome

Logs are:
- Append-only (no modification, no deletion)
- Cryptographically signed
- Backed up to separate storage daily
- Retained for 7 years minimum (regulatory requirement)

---

## CHAPTER 7: BEHAVIORAL SAFEGUARDS

### 7.1 Anti-Emotional Trading
- After ANY loss: mandatory 24h cooldown (no new positions)
- After a big win: NO increasing position size for 7 days
- System explicitly asks: "Is this decision based on data or emotion?"
- "Revenge trading" detection: 3+ trades within 1 hour after loss → halt

### 7.2 Anti-FOMO
- Never buy something that went up > 20% in the last 7 days
- Never buy because "everyone is buying" — only buy on strategy signal
- Crypto pump detection: > 50% rise in 24h → blacklist for 14 days

### 7.3 Anti-Greed
- Take-profit levels MUST be set before entry (not after)
- Never move stop-loss further from entry (only closer)
- "Let it ride" is NOT a valid strategy — predefined exits only

### 7.4 Review Cadence
- Daily: P&L summary, open positions, alerts (automated)
- Weekly: Strategy performance vs benchmark (automated report)
- Monthly: Full portfolio review, rebalancing check (manual review)
- Quarterly: Strategy validity review, regulatory check (manual)
- Annually: Full system audit, security review, tax filing prep

---

## CHAPTER 8: FORBIDDEN ACTIONS

The system MUST NEVER:

1. Use leverage or margin
2. Short sell without hedging
3. Trade derivatives without explicit understanding
4. Invest in assets with < 6 months trading history
5. Chase losses (increase position after loss)
6. Act on tips/rumors/social media hype
7. Override risk limits for any reason
8. Store credentials in plaintext
9. Run without monitoring
10. Execute without logging
11. Trade during system errors
12. Invest emergency funds
13. Concentrate > 20% in single asset
14. Ignore regulatory requirements
15. Skip backtesting for any strategy

---

## CHAPTER 9: DISASTER RECOVERY

### 9.1 System Failure
- If system crashes: all positions remain (broker-side)
- Restart procedure: verify all positions → reconcile → resume monitoring only
- No new trades for 1 hour after system recovery

### 9.2 Broker Failure
- If broker is down: do nothing (positions are safe on exchange)
- Switch to backup broker if available
- Manual access via broker's mobile app as last resort

### 9.3 Market Crash (Black Swan)
- Portfolio drops > 10% in single day: SELL NOTHING (panic selling = locking in loss)
- Wait minimum 48 hours before any action
- Review: is this a systemic crash or single-asset issue?
- If single asset: apply stop-loss rules
- If market-wide: stay put, history shows recovery

### 9.4 Personal Emergency
- System runs autonomously — no intervention needed
- Kill switch accessible from phone (Telegram bot command)
- Trusted contact with kill switch access (dead man's switch)

---

## VERSIONING

- This document is version-controlled
- Any change requires explicit approval
- Changes take effect 7 days after approval (cooling period)
- Emergency changes: immediate but auto-review in 48h

---

*Version: 1.0*
*Created: 2026-05-17*
*Author: Smart Invest System*
*Status: ACTIVE — ALL TRADING MUST COMPLY*
