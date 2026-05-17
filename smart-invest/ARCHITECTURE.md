# Smart Invest Agent — Complete Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SMART INVEST AGENT v1.0                                 │
│                        Capital: ₹50,000 (Test Phase)                             │
└─────────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════════════╗
║                              DATA LAYER                                          ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         ║
║  │Yahoo Finance │  │  CoinDCX     │  │ NSE Bhavcopy │  │ Screener.in  │         ║
║  │              │  │              │  │              │  │              │         ║
║  │• Indian ETFs │  │• BTC price   │  │• EOD prices  │  │• Market cap  │         ║
║  │• US stocks   │  │• ETH price   │  │• All NSE     │  │• PE ratio    │         ║
║  │• Crypto      │  │• All crypto  │  │• Volume data │  │• Revenue     │         ║
║  │• Historical  │  │• Real-time   │  │• Official    │  │• Debt ratio  │         ║
║  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         ║
║         │                  │                  │                  │                 ║
║         └──────────────────┴────────┬─────────┴──────────────────┘                ║
║                                     │                                             ║
║                          ┌──────────▼──────────┐                                  ║
║                          │   DATA AGGREGATOR   │                                  ║
║                          │                     │                                  ║
║                          │ • Price verification│                                  ║
║                          │   (2 sources min)   │                                  ║
║                          │ • Discrepancy >1%   │                                  ║
║                          │   → HALT trading    │                                  ║
║                          └──────────┬──────────┘                                  ║
╚═════════════════════════════════════╪═════════════════════════════════════════════╝
                                      │
╔═════════════════════════════════════╪═════════════════════════════════════════════╗
║                         INTELLIGENCE LAYER                                        ║
╠═════════════════════════════════════╪═════════════════════════════════════════════╣
║                                     │                                             ║
║  ┌──────────────────────────────────▼──────────────────────────────────┐          ║
║  │                        UNIVERSE SCANNER                              │          ║
║  │                                                                      │          ║
║  │  Nifty 100 (50 stocks)  +  AI/IT Sector (15)  +  US AI (10)        │          ║
║  │                                                                      │          ║
║  │  Filters: Market cap > ₹5000Cr │ Volume > 1L │ Price ₹50-₹50000    │          ║
║  └──────────────────────────────────┬──────────────────────────────────┘          ║
║                                     │                                             ║
║                          ┌──────────▼──────────┐                                  ║
║                          │   SCORING ENGINE    │                                  ║
║                          │                     │                                  ║
║                          │ ┌─────────────────┐ │                                  ║
║                          │ │MOMENTUM (25%)   │ │                                  ║
║                          │ │• Above 20d MA?  │ │                                  ║
║                          │ │• Above 50d MA?  │ │                                  ║
║                          │ │• Volume rising? │ │                                  ║
║                          │ │• Outperforming? │ │                                  ║
║                          │ └─────────────────┘ │                                  ║
║                          │ ┌─────────────────┐ │                                  ║
║                          │ │QUALITY (30%)    │ │                                  ║
║                          │ │• Market cap     │ │                                  ║
║                          │ │• Profitable?    │ │                                  ║
║                          │ │• Revenue growth │ │                                  ║
║                          │ │• Low debt?      │ │                                  ║
║                          │ │• ROE > 15%?     │ │                                  ║
║                          │ └─────────────────┘ │                                  ║
║                          │ ┌─────────────────┐ │                                  ║
║                          │ │RISK (25%)       │ │                                  ║
║                          │ │• Low volatility │ │                                  ║
║                          │ │• Max DD < 20%   │ │                                  ║
║                          │ │• No crashes     │ │                                  ║
║                          │ │• Liquid enough? │ │                                  ║
║                          │ └─────────────────┘ │                                  ║
║                          │ ┌─────────────────┐ │                                  ║
║                          │ │TIMING (20%)     │ │                                  ║
║                          │ │• RSI < 70?      │ │                                  ║
║                          │ │• Not at ATH?    │ │                                  ║
║                          │ │• Pullback?      │ │                                  ║
║                          │ │• No FOMO spike? │ │                                  ║
║                          │ └─────────────────┘ │                                  ║
║                          │                     │                                  ║
║                          │  SCORE > 65 = BUY   │                                  ║
║                          │  SCORE > 80 = STRONG │                                  ║
║                          │  SCORE < 50 = AVOID  │                                  ║
║                          └──────────┬──────────┘                                  ║
║                                     │                                             ║
║         ┌───────────────────────────┼───────────────────────────┐                 ║
║         │                           │                           │                 ║
║  ┌──────▼───────┐           ┌───────▼──────┐           ┌───────▼──────┐          ║
║  │  MOMENTUM    │           │MEAN REVERSION│           │     DCA      │          ║
║  │  STRATEGY    │           │  STRATEGY    │           │  STRATEGY    │          ║
║  │              │           │              │           │              │          ║
║  │Buy: cross    │           │Buy: price    │           │Buy: ₹2,500   │          ║
║  │above 20d MA  │           │below lower   │           │every week    │          ║
║  │              │           │Bollinger band│           │regardless    │          ║
║  │Sell: cross   │           │              │           │              │          ║
║  │below 20d MA  │           │Sell: reverts │           │Sell: never   │          ║
║  │              │           │to mean       │           │(long-term)   │          ║
║  └──────┬───────┘           └───────┬──────┘           └───────┬──────┘          ║
║         │                           │                           │                 ║
║         └───────────────────────────┼───────────────────────────┘                 ║
║                                     │                                             ║
║                              TRADE SIGNALS                                        ║
╚═════════════════════════════════════╪═════════════════════════════════════════════╝
                                      │
╔═════════════════════════════════════╪═════════════════════════════════════════════╗
║                          RISK LAYER (THE BIBLE)                                   ║
╠═════════════════════════════════════╪═════════════════════════════════════════════╣
║                                     │                                             ║
║                          ┌──────────▼──────────┐                                  ║
║                          │    RISK ENGINE      │                                  ║
║                          │                     │                                  ║
║                          │ EVERY signal passes │                                  ║
║                          │ through ALL checks: │                                  ║
║                          └──────────┬──────────┘                                  ║
║                                     │                                             ║
║    ┌────────────┬───────────┬───────┼───────┬───────────┬────────────┐            ║
║    │            │           │       │       │           │            │            ║
║    ▼            ▼           ▼       ▼       ▼           ▼            ▼            ║
║ ┌──────┐  ┌────────┐  ┌────────┐┌──────┐┌──────┐ ┌────────┐  ┌─────────┐       ║
║ │Pos   │  │Asset   │  │Circuit ││Cool- ││Anti- │ │Blackout│  │Whitelist│       ║
║ │Size  │  │Class   │  │Breaker ││down  ││FOMO  │ │Hours   │  │Check    │       ║
║ │≤ 5%  │  │≤ 40%   │  │        ││24h   ││>20%  │ │±15min  │  │         │       ║
║ └──┬───┘  └───┬────┘  └───┬────┘└──┬───┘└──┬───┘ └───┬────┘  └────┬────┘       ║
║    │           │           │        │       │         │            │             ║
║    └───────────┴───────────┴────┬───┴───────┴─────────┴────────────┘             ║
║                                 │                                                 ║
║              ┌─────────────┐    │    ┌─────────────┐                              ║
║              │  APPROVED   │◄───┴───►│  REJECTED   │                              ║
║              └──────┬──────┘         └──────┬──────┘                              ║
║                     │                       │                                     ║
║                     │               ┌───────▼───────┐                             ║
║                     │               │ Log reason    │                             ║
║                     │               │ Alert user    │                             ║
║                     │               │ DO NOTHING    │                             ║
║                     │               └───────────────┘                             ║
║                     │                                                             ║
║    ┌────────────────┼────────────────────────────────────────┐                    ║
║    │     CIRCUIT BREAKERS (Auto-Trigger)                      │                    ║
║    │                                                          │                    ║
║    │  Single trade loss > 1%  ──→  Close position             │                    ║
║    │  Daily loss > 2%         ──→  HALT 24 hours              │                    ║
║    │  Weekly loss > 5%        ──→  HALT 7 days                │                    ║
║    │  Monthly loss > 8%       ──→  HALT + full review         │                    ║
║    │  Total drawdown > 15%    ──→  ☠️ KILL SWITCH              │                    ║
║    │                                                          │                    ║
║    └──────────────────────────────────────────────────────────┘                    ║
╚═════════════════════════════════════╪═════════════════════════════════════════════╝
                                      │
╔═════════════════════════════════════╪═════════════════════════════════════════════╗
║                         EXECUTION LAYER                                           ║
╠═════════════════════════════════════╪═════════════════════════════════════════════╣
║                                     │                                             ║
║              ┌──────────────────────┼──────────────────────┐                      ║
║              │                      │                      │                      ║
║       ┌──────▼───────┐      ┌───────▼──────┐      ┌───────▼──────┐               ║
║       │  PAPER MODE  │      │  Angel One   │      │   CoinDCX    │               ║
║       │              │      │  SmartAPI    │      │     API      │               ║
║       │ Simulates    │      │              │      │              │               ║
║       │ trades with  │      │• Indian ETFs │      │• BTC/INR     │               ║
║       │ real prices  │      │• NIFTYBEES   │      │• ETH/INR     │               ║
║       │              │      │• ITBEES      │      │              │               ║
║       │ NO real $    │      │• BANKBEES    │      │ Limit orders │               ║
║       │              │      │              │      │ only (never  │               ║
║       │ First 6      │      │ LIMIT orders │      │ market)      │               ║
║       │ months       │      │ DAY validity │      │              │               ║
║       └──────────────┘      │ DELIVERY only│      └──────────────┘               ║
║                             │ (no margin)  │                                      ║
║                             └──────────────┘                                      ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════════════════╗
║                         MONITORING LAYER                                          ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐   ║
║  │  TELEGRAM BOT   │    │   DASHBOARD     │    │        SCHEDULER            │   ║
║  │                 │    │                 │    │                             │   ║
║  │ Alerts:         │    │ localhost:5050  │    │ Every 1 min:  price update  │   ║
║  │ • Trade exec    │    │                 │    │ Every 5 min:  reconcile     │   ║
║  │ • Circuit break │    │ • Portfolio $   │    │ 9:20 AM:      morning scan  │   ║
║  │ • Kill switch   │    │ • P&L chart     │    │ 3:45 PM:      EOD summary   │   ║
║  │ • Daily P&L     │    │ • Positions     │    │ Saturday:     weekly report  │   ║
║  │ • Weekly report │    │ • Signals       │    │ 1st month:    monthly review │   ║
║  │                 │    │ • Health score  │    │                             │   ║
║  │ Commands:       │    │                 │    │ Auto-refreshes every 30s    │   ║
║  │ • /status       │    │ Dark theme UI   │    │                             │   ║
║  │ • /positions    │    │ Auto-refresh    │    └─────────────────────────────┘   ║
║  │ • /kill         │    │                 │                                       ║
║  │ • /pause        │    └─────────────────┘                                       ║
║  │ • /resume       │                                                              ║
║  │ • /score SYMBOL │                                                              ║
║  └─────────────────┘                                                              ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════════════════╗
║                         VALIDATION LAYER                                          ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  Before ANY strategy goes live, it MUST pass:                                     ║
║                                                                                   ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         ║
║  │  10-YEAR     │  │   STRESS     │  │ MONTE CARLO  │  │WALK-FORWARD  │         ║
║  │  BACKTEST    │  │   TESTS      │  │              │  │              │         ║
║  │              │  │              │  │ 10,000 random│  │ Train: 70%   │         ║
║  │ Sharpe > 1.0 │  │ • 2008 crash │  │ simulations  │  │ Test:  30%   │         ║
║  │ MaxDD < 20%  │  │ • 2020 COVID │  │              │  │              │         ║
║  │ Win rate     │  │ • 2022 crypto│  │ 95% must be  │  │ Degradation  │         ║
║  │ Profit factor│  │ • Demonet.   │  │ profitable   │  │ must be <20% │         ║
║  │              │  │              │  │              │  │              │         ║
║  │ ALL must     │  │ Survive with │  │ Proves skill │  │ Proves       │         ║
║  │ pass ✅       │  │ DD < 20% ✅   │  │ not luck ✅   │  │ robustness ✅ │         ║
║  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         ║
║                                                                                   ║
║                    ALL 4 MUST PASS → then 6 months paper → then live              ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════════════════╗
║                         REBALANCING & TAX                                         ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  Target Allocation:                    Tax Awareness:                             ║
║  ┌─────────────────────────┐          ┌─────────────────────────────┐            ║
║  │ Stocks:     50% ████████│          │ Hold > 1 year → LTCG 12.5% │            ║
║  │ Crypto:     30% █████   │          │ Hold < 1 year → STCG 20%   │            ║
║  │ Opportunity:10% ██      │          │ Crypto: always 30% flat     │            ║
║  │ Cash:       10% ██      │          │                             │            ║
║  └─────────────────────────┘          │ Sells LTCG positions first  │            ║
║                                        │ Sells winners before losers │            ║
║  If drift > 5% from target → auto-    │ First ₹1.25L LTCG tax-free │            ║
║  rebalance (sell overweight,           └─────────────────────────────┘            ║
║  buy underweight)                                                                 ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════════════════╗
║                         SAFETY FEATURES                                           ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  🛡️  IMMUTABLE AUDIT LOG — every event timestamped, append-only                   ║
║  🛡️  KILL SWITCH — accessible via Telegram, dashboard, or auto-trigger            ║
║  🛡️  PAPER MODE FIRST — 6 months simulated before real money                      ║
║  🛡️  24h COOLDOWN — no new trades after any loss                                  ║
║  🛡️  ANTI-FOMO — never buys >20% spike in 7 days                                 ║
║  🛡️  ANTI-REVENGE — detects 3+ trades after loss → halt                           ║
║  🛡️  POSITION RECONCILIATION — every 5 min verifies broker matches                ║
║  🛡️  PRICE VERIFICATION — 2 sources must agree within 1%                          ║
║  🛡️  NO LEVERAGE — cash delivery only, no margin ever                             ║
║  🛡️  NO MARKET ORDERS — limit orders only (prevents slippage)                     ║
║  🛡️  WHITELIST ONLY — can only buy pre-approved assets                            ║
║  🛡️  FORBIDDEN LIST — no derivatives, no penny stocks, no new tokens              ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

                              ┌─────────────────┐
                              │   HOW IT RUNS   │
                              └────────┬────────┘
                                       │
                    ┌──────────────────────────────────────┐
                    │                                      │
                    │   $ python main.py                   │
                    │                                      │
                    │   1. Starts in PAPER mode            │
                    │   2. Connects data feeds             │
                    │   3. Launches scheduler              │
                    │   4. Launches dashboard (port 5050)  │
                    │   5. Polls Telegram for commands     │
                    │   6. Scans → Scores → Signals        │
                    │   7. Risk checks every signal        │
                    │   8. Executes (paper or live)        │
                    │   9. Logs everything                 │
                    │  10. Alerts via Telegram             │
                    │                                      │
                    │   Runs 24/7 autonomously             │
                    │   Kill switch always accessible      │
                    │                                      │
                    └──────────────────────────────────────┘
```
