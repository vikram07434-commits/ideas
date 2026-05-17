# Smart Invest

> AI-powered investment automation using Playwright — every penny counts

## Vision

An intelligent automation system that acts **as you** on investment portals — researching, monitoring, and executing investment decisions with extreme precision. Every small loss is treated as a critical failure. The system should be paranoid about protecting capital.

## Philosophy

- **Every penny matters** — no loss is too small to care about
- **Act like the owner** — this is YOUR money, not play money
- **Safety first** — never YOLO, always validate before acting
- **Automate the tedious** — research, monitoring, rebalancing, alerts
- **Human-in-the-loop for big decisions** — automation suggests, you confirm

## Core Features

- **Portal Automation (Playwright)** — Log in, navigate, extract data, execute trades
- **Market Research** — Scan for opportunities, compare options, track performance
- **Risk Monitoring** — Alert on losses, track portfolio health, stop-loss triggers
- **Smart Alerts** — Notify on price drops, opportunities, anomalies
- **Decision Support** — Present options with risk/reward analysis before any action
- **Audit Trail** — Log every action, every decision, every penny moved

## Research Needed

- [ ] Identify the best investment portal(s) to automate (Zerodha? Groww? Interactive Brokers?)
- [ ] Understand portal APIs vs Playwright scraping tradeoffs
- [ ] Legal/ToS considerations for automation
- [ ] Define investment strategy to automate (SIP, swing trading, rebalancing?)
- [ ] Security — credential management, 2FA handling

## Tech Stack (TBD)

- Automation: Playwright (Python or Node.js)
- Backend: Python (analysis, decision engine)
- Alerts: Telegram bot / email / push notifications
- Database: SQLite or PostgreSQL (transaction log, portfolio state)
- Scheduler: Cron / systemd timers for regular checks

## Safety Rules (NON-NEGOTIABLE)

1. **Never execute a trade without explicit confirmation** (until trust is established)
2. **Always show expected outcome before acting**
3. **Hard stop-loss limits** — auto-alert if portfolio drops beyond threshold
4. **Dry-run mode** — simulate all actions first
5. **Audit everything** — no action goes unlogged
6. **Credential security** — encrypted, never in code, never in git

## Status

- [ ] Research best portals and their automation-friendliness
- [ ] Decide: India-focused (Zerodha/Groww) or international (IBKR)?
- [ ] Legal research on automation ToS
- [ ] Build basic Playwright login + data extraction PoC

---

*Created: 2026-05-17*
