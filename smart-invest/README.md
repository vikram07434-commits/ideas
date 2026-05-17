# Smart Invest

> AI-powered investment automation — every penny counts, zero tolerance for loss

## Vision

An intelligent automation system that acts **as you** on investment portals — researching, monitoring, and executing investment decisions with extreme precision. Every small loss is treated as a critical failure. The system should be paranoid about protecting capital.

This is not a toy. This is not a hobby project. This handles real money.

---

## Philosophy (THE BIBLE)

These principles are absolute. No code gets written, no strategy gets deployed, no trade gets executed unless it passes every single one of these checks. Violation of any principle = immediate system halt.

### The 5 Commandments

1. **Capital preservation above all** — making money is secondary to not losing money
2. **Every penny matters** — a 0.01% unnecessary loss at scale is unacceptable
3. **Prove it before you trust it** — no strategy goes live without exhaustive proof
4. **The system serves you, not the other way around** — human override always available
5. **If in doubt, do nothing** — inaction is always safer than wrong action

---

## RISK PROTOCOLS (NON-NEGOTIABLE — TREAT AS LAW)

### A. Capital Protection Rules

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | Never invest more than you can afford to lose | Hard capital allocation limit in config — system cannot exceed it |
| 2 | Maximum single position size: 5% of total portfolio | Code-enforced, cannot be bypassed |
| 3 | Maximum drawdown limit: 10% of portfolio | Auto-kill switch — halts ALL trading instantly |
| 4 | Daily loss limit: 2% of portfolio | Breached = system shuts down for 24h minimum |
| 5 | No margin/leverage trading | Hardcoded restriction — system physically cannot use leverage |
| 6 | Emergency fund untouchable | Separate from investment capital, never accessed by system |
| 7 | No single asset > 20% of portfolio | Auto-rebalance triggered if breached |

### B. Strategy Validation Rules (Before ANY strategy goes live)

| # | Rule | Minimum Threshold |
|---|------|-------------------|
| 1 | Backtesting on historical data | Minimum 10 years of data |
| 2 | Out-of-sample testing | Minimum 3 years unseen data |
| 3 | Paper trading (simulation) | Minimum 6 months with real market conditions |
| 4 | Walk-forward analysis | Must pass on rolling windows |
| 5 | Stress testing (crash scenarios) | Must survive 2008, 2020 COVID, 2022 crypto winter |
| 6 | Monte Carlo simulation | 10,000 runs, 95th percentile must be profitable |
| 7 | Survivorship bias check | Data must include delisted/failed assets |
| 8 | Slippage modeling | Assume 0.1-0.5% slippage on every trade |
| 9 | Fee/commission modeling | All costs included in P&L calculation |
| 10 | Tax impact modeling | Post-tax returns must be positive |

### C. Diversification Rules

| # | Rule | Rationale |
|---|------|-----------|
| 1 | Minimum 3 uncorrelated asset classes | Stocks, bonds, gold, crypto, real estate |
| 2 | Geographic diversification | No single country > 60% exposure |
| 3 | Strategy diversification | Minimum 2 independent strategies running |
| 4 | Time diversification | Never deploy all capital at once — dollar-cost average |
| 5 | Correlation monitoring | Alert if portfolio correlation exceeds 0.7 |
| 6 | Sector limits | No single sector > 25% |

### D. Technical Safety (System Architecture)

| # | Rule | Implementation |
|---|------|---------------|
| 1 | No single point of failure | Redundant monitoring, failover systems |
| 2 | Circuit breakers | Auto-halt on: API errors, price anomalies, connectivity loss |
| 3 | Stale data detection | If market data > 30s old, halt all decisions |
| 4 | Rate limiting | Never exceed API limits, backoff exponentially |
| 5 | Idempotent operations | Same action cannot execute twice accidentally |
| 6 | Atomic transactions | Trade either fully executes or fully rolls back |
| 7 | Health monitoring | System checks itself every 60s, alerts on anomaly |
| 8 | Graceful degradation | If subsystem fails, others continue safely |
| 9 | Kill switch | One command stops everything instantly |
| 10 | Watchdog timer | If system doesn't heartbeat in 5min, auto-shutdown |

### E. Security Protocols (Bank-Grade)

| # | Rule | Implementation |
|---|------|---------------|
| 1 | Credentials encrypted at rest | AES-256 encryption, never plaintext |
| 2 | 2FA/TOTP for all portal access | Hardware key preferred, software TOTP minimum |
| 3 | API keys rotated every 30 days | Automated rotation with zero downtime |
| 4 | No credentials in code or git | Environment variables or encrypted vault only |
| 5 | Network security | All connections TLS 1.3+, certificate pinning |
| 6 | IP whitelisting | Trading only from known, static IPs |
| 7 | Session management | Auto-logout after inactivity, token expiry |
| 8 | Audit logging | Every authentication, every action, immutable logs |
| 9 | Principle of least privilege | Each component has minimum required access |
| 10 | Intrusion detection | Alert on unexpected login locations/patterns |

### F. Regulatory & Legal Compliance

| # | Rule | Jurisdiction |
|---|------|-------------|
| 1 | SEBI compliance for India algo trading | Mandatory — retail algo must go through broker APIs |
| 2 | Broker ToS compliance | Never violate platform terms of service |
| 3 | Tax reporting built-in | Auto-calculate capital gains (short/long term) |
| 4 | KYC requirements respected | Never circumvent identity verification |
| 5 | No market manipulation | No wash trading, spoofing, or front-running |
| 6 | Record keeping (7 years) | All transactions archived per regulatory requirements |
| 7 | Cross-border regulations | Comply with FEMA for international investments from India |

### G. Behavioral Safeguards (Protecting from Human Weakness)

| # | Rule | How |
|---|------|-----|
| 1 | No revenge trading | After a loss, mandatory 24h cooldown before new positions |
| 2 | No FOMO trading | Strategy-only — never chase a pump |
| 3 | No overriding the system in greed | Manual override requires 2-step confirmation + reason logging |
| 4 | Position sizing by algorithm only | Kelly criterion or fractional Kelly — never "gut feel" |
| 5 | Regular review cadence | Weekly performance review, monthly strategy review |
| 6 | Emotional state check | Before manual override, confirm: "Am I acting on data or emotion?" |

---

## ARCHITECTURE (High-Level)

```
┌─────────────────────────────────────────────────────────┐
│                    SMART INVEST                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Market  │  │ Strategy │  │   Risk   │             │
│  │  Data    │──│  Engine  │──│  Engine  │             │
│  │  Feed    │  │          │  │          │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│       │              │              │                   │
│       ▼              ▼              ▼                   │
│  ┌──────────────────────────────────────┐              │
│  │         DECISION ENGINE             │              │
│  │  (Only executes if ALL checks pass) │              │
│  └──────────────────────────────────────┘              │
│                      │                                  │
│                      ▼                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Circuit │  │  Order   │  │  Audit   │             │
│  │  Breaker │──│ Executor │──│  Logger  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                      │                                  │
│                      ▼                                  │
│  ┌──────────────────────────────────────┐              │
│  │     PORTAL AUTOMATION (Playwright)   │              │
│  │     or BROKER API (Zerodha/Groww)    │              │
│  └──────────────────────────────────────┘              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  MONITORING: Health │ Alerts │ Dashboard │ Kill Switch  │
└─────────────────────────────────────────────────────────┘
```

---

## RESEARCH PHASE (Current)

### What I'm Investigating

- [ ] **Best platforms** — which portals allow automation legally and safely
- [ ] **API vs Playwright** — official APIs (lower risk) vs browser automation (fragile)
- [ ] **Asset classes** — stocks, mutual funds, ETFs, crypto, or combination
- [ ] **Strategies** — only battle-tested, academically-proven approaches
- [ ] **Indian market specifics** — SEBI rules, tax (STT, LTCG, STCG), broker APIs
- [ ] **International options** — crypto exchanges, US markets via IBKR
- [ ] **Open source projects** — learn from proven codebases (not trust blindly)

### Source Credibility Filter

Before trusting ANY information source, it must pass:

| Check | Criteria |
|-------|----------|
| **Who** | Real person with verifiable track record? Not anonymous guru? |
| **Proof** | Audited returns? Verified P&L? Not just screenshots? |
| **Time** | Strategy profitable for 3+ years? Not just last month? |
| **Community** | Peer-reviewed? Criticized and survived scrutiny? |
| **Conflicts** | Are they selling something? Affiliate links? Course promotion? |
| **Reproducibility** | Can the strategy be independently backtested and verified? |
| **Survivorship** | Are they showing ALL trades or cherry-picking winners? |

---

## TECH STACK (Planned)

| Component | Technology | Why |
|-----------|-----------|-----|
| Core Language | Python 3.12+ | Rich finance ecosystem, async support |
| Browser Automation | Playwright | Headless, reliable, multi-browser |
| Broker API | Zerodha Kite / Groww API / Angel SmartAPI | Official, SEBI-compliant |
| Data Storage | PostgreSQL | ACID compliance, time-series support |
| Cache | Redis | Fast state, rate limiting |
| Task Scheduler | Celery + Redis | Reliable async task execution |
| Monitoring | Prometheus + Grafana | Real-time system health |
| Alerts | Telegram Bot + Email | Instant notification on events |
| Secrets | HashiCorp Vault or age encryption | Zero plaintext credentials |
| Backtesting | Backtrader / Zipline / custom | Strategy validation |
| Logging | Structured JSON logs | Immutable audit trail |
| Deployment | Docker + systemd | Reproducible, auto-restart |

---

## INVESTMENT APPROACHES UNDER CONSIDERATION

### Tier 1: Ultra-Low Risk (Capital Preservation Focus)
- Systematic SIP with intelligent timing (buy more on dips)
- Index fund rebalancing (Nifty 50, S&P 500)
- Debt fund allocation with interest rate monitoring
- Gold allocation as hedge (Sovereign Gold Bonds / Gold ETF)

### Tier 2: Low-Medium Risk (Growth with Safety)
- Mean reversion strategies on large-cap stocks
- Momentum strategies with strict stop-losses
- Dividend harvesting with reinvestment
- Crypto DCA (Dollar Cost Averaging) on BTC/ETH only

### Tier 3: Medium Risk (Only with proven edge)
- Statistical arbitrage (pairs trading)
- Event-driven strategies (earnings, dividends)
- Volatility-based position sizing
- Cross-exchange crypto arbitrage

### NEVER (Forbidden Strategies)
- Day trading / scalping (fees eat profits for retail)
- Options selling without hedge (unlimited downside)
- Penny stocks / micro-caps (manipulation risk)
- Meme coins / shitcoins (gambling, not investing)
- Leverage / margin (amplifies losses)
- Any strategy without 10-year backtest proof

---

## DEVELOPMENT PHASES

### Phase 0: Foundation (Current)
- [ ] Deep research — platforms, strategies, regulations
- [ ] Source credibility verification
- [ ] Architecture design document
- [ ] Security threat modeling

### Phase 1: Infrastructure
- [ ] Set up project skeleton (Python, Docker, CI/CD)
- [ ] Implement credential vault
- [ ] Build audit logging system
- [ ] Create kill switch mechanism
- [ ] Set up monitoring and alerting

### Phase 2: Data Collection
- [ ] Connect to market data feeds
- [ ] Build historical data pipeline
- [ ] Implement stale data detection
- [ ] Create data validation layer

### Phase 3: Strategy Engine
- [ ] Implement backtesting framework
- [ ] Code first strategy (SIP timing optimization)
- [ ] Run 10-year backtest
- [ ] Monte Carlo validation
- [ ] Stress test against crash scenarios

### Phase 4: Paper Trading
- [ ] Connect to broker sandbox/paper account
- [ ] Run strategy for 6 months minimum
- [ ] Track all metrics: Sharpe, Sortino, max drawdown
- [ ] Compare against simple buy-and-hold benchmark

### Phase 5: Live (Micro Capital)
- [ ] Deploy with MINIMUM capital (₹1000 or equivalent)
- [ ] Monitor for 3 months
- [ ] Validate paper trading results match live
- [ ] Gradually scale capital if proven

### Phase 6: Scale
- [ ] Increase capital in 10% increments only
- [ ] Add second strategy
- [ ] Add second asset class
- [ ] Multi-broker support

---

## KEY METRICS TO TRACK

| Metric | Target | Kill Threshold |
|--------|--------|---------------|
| Sharpe Ratio | > 1.5 | < 0.5 → disable strategy |
| Max Drawdown | < 10% | > 15% → halt everything |
| Win Rate | > 55% | < 45% over 100 trades → review |
| Profit Factor | > 1.5 | < 1.0 → disable immediately |
| Daily VaR (95%) | < 2% portfolio | > 3% → reduce positions |
| Recovery Time | < 30 days from drawdown | > 60 days → strategy review |
| System Uptime | > 99.5% | < 95% → fix infrastructure |

---

## WHAT I DO NOT KNOW (Honest Assessment)

I (the user) have zero investment knowledge. This means:
- The system must be self-educating — explain every decision in plain language
- No jargon without explanation in the UI
- Every trade must show: "Why am I doing this? What can go wrong? What's my exit?"
- The system must protect me from my own ignorance
- Conservative defaults — I'd rather miss gains than take unnecessary risks

---

*Created: 2026-05-17*
*Last Updated: 2026-05-17*
*Status: Research Phase — NO live trading until all protocols satisfied*
