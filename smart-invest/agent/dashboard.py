"""
Smart Invest Agent — Web Dashboard
Simple Flask app showing portfolio status, P&L, positions, signals.
Runs locally at http://localhost:5050
"""

from flask import Flask, render_template_string, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

# Will be injected by main.py when starting
agent_instance = None
DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET", "change-me-in-env")

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Invest Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 1px solid #333; }
        .header h1 { font-size: 24px; color: #fff; }
        .state { padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; }
        .state-paper { background: #1a3a5c; color: #5bb5f7; }
        .state-active { background: #1a3c1a; color: #5bf75b; }
        .state-halted { background: #5c3a1a; color: #f7a55b; }
        .state-killed { background: #5c1a1a; color: #f75b5b; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .card { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 20px; }
        .card-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .card-value { font-size: 28px; font-weight: 700; margin-top: 5px; }
        .positive { color: #4caf50; }
        .negative { color: #f44336; }
        .neutral { color: #fff; }
        table { width: 100%; border-collapse: collapse; background: #1a1a1a; border-radius: 12px; overflow: hidden; }
        th { background: #252525; padding: 12px 16px; text-align: left; font-size: 12px; color: #888; text-transform: uppercase; }
        td { padding: 12px 16px; border-top: 1px solid #2a2a2a; }
        .section-title { font-size: 18px; margin: 30px 0 15px; color: #fff; }
        .signal-buy { color: #4caf50; font-weight: 600; }
        .signal-sell { color: #f44336; font-weight: 600; }
        .signal-reject { color: #888; text-decoration: line-through; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Smart Invest</h1>
        <span class="state state-{{ state }}">{{ state | upper }}</span>
    </div>

    <div class="cards">
        <div class="card">
            <div class="card-label">Portfolio Value</div>
            <div class="card-value neutral">₹{{ "%.0f"|format(portfolio_value) }}</div>
        </div>
        <div class="card">
            <div class="card-label">Daily P&L</div>
            <div class="card-value {{ 'positive' if daily_pnl >= 0 else 'negative' }}">
                {{ "+" if daily_pnl >= 0 else "" }}₹{{ "%.0f"|format(daily_pnl) }}
            </div>
        </div>
        <div class="card">
            <div class="card-label">Drawdown</div>
            <div class="card-value {{ 'negative' if drawdown > 5 else 'neutral' }}">{{ "%.1f"|format(drawdown) }}%</div>
        </div>
        <div class="card">
            <div class="card-label">Open Positions</div>
            <div class="card-value neutral">{{ positions | length }}</div>
        </div>
        <div class="card">
            <div class="card-label">Cash Reserve</div>
            <div class="card-value neutral">₹{{ "%.0f"|format(cash) }}</div>
        </div>
    </div>

    <h2 class="section-title">Open Positions</h2>
    <table>
        <thead><tr><th>Symbol</th><th>Type</th><th>Qty</th><th>Entry</th><th>Current</th><th>P&L</th><th>P&L %</th></tr></thead>
        <tbody>
        {% for p in positions %}
        <tr>
            <td>{{ p.symbol }}</td>
            <td>{{ p.asset_class }}</td>
            <td>{{ "%.4f"|format(p.quantity) }}</td>
            <td>₹{{ "%.2f"|format(p.entry_price) }}</td>
            <td>₹{{ "%.2f"|format(p.current_price) }}</td>
            <td class="{{ 'positive' if p.pnl >= 0 else 'negative' }}">₹{{ "%.0f"|format(p.pnl) }}</td>
            <td class="{{ 'positive' if p.pnl_pct >= 0 else 'negative' }}">{{ "%.1f"|format(p.pnl_pct * 100) }}%</td>
        </tr>
        {% endfor %}
        {% if not positions %}<tr><td colspan="7" style="text-align:center;color:#666;">No open positions</td></tr>{% endif %}
        </tbody>
    </table>

    <h2 class="section-title">Recent Signals</h2>
    <table>
        <thead><tr><th>Time</th><th>Symbol</th><th>Action</th><th>Price</th><th>Status</th><th>Reason</th></tr></thead>
        <tbody>
        {% for s in signals %}
        <tr>
            <td>{{ s.time }}</td>
            <td>{{ s.symbol }}</td>
            <td class="signal-{{ s.action }}">{{ s.action | upper }}</td>
            <td>₹{{ "%.2f"|format(s.price) }}</td>
            <td class="{{ 'signal-buy' if s.status == 'executed' else 'signal-reject' }}">{{ s.status }}</td>
            <td>{{ s.reason }}</td>
        </tr>
        {% endfor %}
        {% if not signals %}<tr><td colspan="6" style="text-align:center;color:#666;">No signals yet</td></tr>{% endif %}
        </tbody>
    </table>

    <p style="margin-top:40px;color:#555;font-size:12px;">
        Last updated: {{ updated }} | Auto-refreshes every 30s
    </p>
</body>
</html>
"""


@app.route("/")
def dashboard():
    if agent_instance is None:
        return "Agent not connected", 503

    health = agent_instance.health_check()
    return render_template_string(DASHBOARD_HTML,
        state=health["state"],
        portfolio_value=health["portfolio_value"],
        daily_pnl=health["daily_pnl"],
        drawdown=health["drawdown_pct"],
        positions=agent_instance.positions,
        cash=health["portfolio_value"] * 0.1,  # Approximate
        signals=getattr(agent_instance, "recent_signals", []),
        updated=datetime.utcnow().strftime("%H:%M:%S UTC"),
    )


@app.route("/api/health")
def api_health():
    if agent_instance is None:
        return jsonify({"error": "agent not running"}), 503
    return jsonify(agent_instance.health_check())


@app.route("/api/positions")
def api_positions():
    if agent_instance is None:
        return jsonify([])
    return jsonify([{
        "symbol": p.symbol,
        "asset_class": p.asset_class.value,
        "quantity": p.quantity,
        "entry_price": p.entry_price,
        "current_price": p.current_price,
        "pnl": p.pnl,
        "pnl_pct": p.pnl_pct,
    } for p in agent_instance.positions])


@app.route("/api/kill", methods=["POST"])
def api_kill():
    if agent_instance is None:
        return jsonify({"error": "agent not running"}), 503
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != DASHBOARD_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    agent_instance.risk_engine._trigger_kill_switch()
    return jsonify({"status": "killed"})


def start_dashboard(agent, port: int = 5050):
    global agent_instance
    agent_instance = agent
    app.run(host="127.0.0.1", port=port, debug=False)
