# HyperSignals Assessment — Against RISK-PROTOCOLS.md

> Date: 2026-05-17
> Platform: https://app.hypersignals.ai
> Assessment: CRITICAL REVIEW

---

## What HyperSignals Is

- Copy-trading platform for crypto markets
- Connect your wallet (0x address) and mirror trader positions
- Traders visible with metrics: AUM, Sharpe ratio, Profit Factor, Max DD, Total PnL, ROI
- Categories: Holder (long-term), Swinger (medium-term), Flipper (short-term)
- Top performer claims: $49.7M AUM, Sharpe 8.94, Profit Factor 5.11, Max DD 6.1%

---

## RED FLAGS — Protocol Violations

### CRITICAL: Violates Chapter 8 (Forbidden Actions)

| Rule | Violation |
|------|-----------|
| #6: Act on tips/rumors/social media hype | Copy-trading IS following someone else blindly |
| #4: Invest in assets with < 6 months history | Many crypto tokens listed are brand new |
| #3: Trade derivatives without understanding | Crypto perpetuals/leveraged positions common |
| #1: Use leverage or margin | Many "top traders" use leverage (visible in their PnL patterns) |

### CRITICAL: Violates Chapter 2 (Strategy Rules)

- **No backtest possible** — you're copying someone else's unknown strategy
- **Cannot stress-test** — you don't know the trader's logic
- **No independent verification** — results shown on THEIR platform, not auditable
- **6-month paper trading impossible** — the trader's strategy could change any day
- **You don't know the fee model** — hidden fees in spread, execution, platform cuts

### CRITICAL: Violates Chapter 1 (Capital Rules)

- **No position sizing control** — you mirror whatever they do
- **No circuit breakers on their trades** — if they go all-in, you go all-in
- **No stop-loss guarantee** — depends on the copied trader setting stops
- **Kill switch depends on you reacting** — by the time you see it, damage is done

### CRITICAL: Violates Chapter 4 (Security Rules)

- **Wallet connection required** — grants smart contract permissions
- **Smart contract risk** — one vulnerability = total fund loss
- **No IP restriction possible** — blockchain is permissionless
- **Token approval exploits** — unlimited approvals can drain wallet
- **Platform could rug-pull** — what's their legal entity? Where incorporated?

---

## Credibility Assessment

### What We DON'T Know (Must Know Before Trusting)

1. **Who built it?** — No team page visible, no LinkedIn profiles linked
2. **How long running?** — No verifiable launch date
3. **Are results on-chain verifiable?** — Wallet addresses shown but could be selective
4. **Survivorship bias?** — Are failed traders removed from leaderboard?
5. **Is AUM real?** — $49.7M AUM could be spoofed or include the platform's own funds
6. **Regulatory status?** — Is this registered anywhere? Any license?
7. **Audit history?** — Smart contracts audited by whom? Report public?
8. **Track record during crashes?** — How did top traders perform in 2022 crypto winter?
9. **Community size?** — Reddit/Discord/Twitter following? Real users sharing results?
10. **Insurance/guarantee?** — What happens if smart contract gets hacked?

### Sharpe Ratio of 8.94 — EXTREME RED FLAG

- Warren Buffett's lifetime Sharpe: ~0.76
- Renaissance Technologies (best hedge fund ever): ~2.0-3.0
- A Sharpe of 8.94 is either:
  - **Fraud** (fabricated numbers)
  - **Survivorship bias** (only showing best period)
  - **Unsustainable** (will mean-revert violently)
  - **Leverage-inflated** (violates our Rule #1)

**No legitimate strategy has a sustained Sharpe > 3.0.** This alone is disqualifying.

---

## Verdict: DO NOT USE

### Summary of Protocol Violations

| Protocol Chapter | Violations | Severity |
|-----------------|------------|----------|
| Chapter 1: Capital Rules | 4 violations | CRITICAL |
| Chapter 2: Strategy Rules | 5 violations | CRITICAL |
| Chapter 3: Execution Rules | 3 violations | HIGH |
| Chapter 4: Security Rules | 5 violations | CRITICAL |
| Chapter 7: Behavioral Safeguards | 2 violations | HIGH |
| Chapter 8: Forbidden Actions | 4 violations | CRITICAL |

**Total: 23 protocol violations. This platform is incompatible with our system.**

### Specific Reasons

1. **Copy-trading = giving up all control** — our protocols require us to UNDERSTAND and VERIFY every strategy
2. **Crypto wallet connections = attack surface** — smart contract exploits can drain funds instantly
3. **Unverifiable track records** — Sharpe 8.94 is mathematically suspicious
4. **No regulatory protection** — if they disappear, money is gone forever
5. **Violates the PREAMBLE** — "system's PRIMARY job is to NOT LOSE MONEY" — handing control to anonymous traders is the opposite

---

## What Copy-Trading Would Need to Pass Our Protocols

If we EVER consider copy-trading in the future, it would need:

1. Regulated platform (SEC/SEBI/FCA licensed)
2. Verifiable, audited track record (minimum 3 years, through at least one crash)
3. On-chain proof with independent verification
4. Ability to set OUR OWN stop-losses that override the trader
5. Position sizing controls on our end
6. Smart contract audited by Trail of Bits / OpenZeppelin / Certora
7. Insurance fund for smart contract failures
8. No unlimited token approvals — exact amounts only
9. Track record showing Sharpe < 3.0 (realistic, not fabricated)
10. Kill switch that executes in < 1 second

**HyperSignals meets ZERO of these 10 requirements.**

---

*Assessment by: Smart Invest Risk Analysis Engine*
*Status: REJECTED — DO NOT INVEST*
