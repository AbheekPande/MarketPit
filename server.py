"""
MarketPit — Python Backend Server
Fetches real-time Indian stock data from Yahoo Finance (yfinance)
and serves it to the frontend via a local REST API.

Run:  python server.py
Then open marketpit.html in your browser.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import threading
import time
import os
import json
try:
    import requests as req_lib
except ImportError:
    req_lib = None

app = Flask(__name__)
CORS(app)  # Allow requests from the HTML frontend

# ── Indian Stock Symbols (NSE via Yahoo Finance) ──
# Yahoo Finance uses ".NS" suffix for NSE and ".BO" for BSE
INDIAN_STOCKS = [
    {"sym": "RELIANCE",  "yf": "RELIANCE.NS",  "name": "Reliance Industries"},
    {"sym": "TCS",       "yf": "TCS.NS",        "name": "Tata Consultancy"},
    {"sym": "HDFCBANK",  "yf": "HDFCBANK.NS",   "name": "HDFC Bank"},
    {"sym": "INFY",      "yf": "INFY.NS",        "name": "Infosys"},
    {"sym": "ICICIBANK", "yf": "ICICIBANK.NS",   "name": "ICICI Bank"},
    {"sym": "HINDUNILVR","yf": "HINDUNILVR.NS",  "name": "Hindustan Unilever"},
    {"sym": "ITC",       "yf": "ITC.NS",         "name": "ITC Ltd"},
    {"sym": "SBIN",      "yf": "SBIN.NS",        "name": "State Bank of India"},
    {"sym": "BAJFINANCE","yf": "BAJFINANCE.NS",  "name": "Bajaj Finance"},
    {"sym": "WIPRO",     "yf": "WIPRO.NS",       "name": "Wipro Ltd"},
]

# ── Index Symbols ──
INDICES = [
    {"sym": "NIFTY 50",   "yf": "^NSEI",  "name": "Nifty 50"},
    {"sym": "SENSEX",     "yf": "^BSESN", "name": "BSE Sensex"},
    {"sym": "NIFTY BANK", "yf": "^NSEBANK","name": "Nifty Bank"},
    {"sym": "BTC-USD",    "yf": "BTC-USD","name": "Bitcoin"},
    {"sym": "GOLD",       "yf": "GC=F",   "name": "Gold Futures"},
]

# ── Cache so we don't hammer Yahoo Finance ──
_cache = {"stocks": [], "indices": [], "last_updated": None}
_cache_lock = threading.Lock()
CACHE_TTL = 60  # seconds


def fetch_quote(symbol_yf):
    """Fetch latest quote for a single Yahoo Finance symbol."""
    try:
        ticker = yf.Ticker(symbol_yf)
        info = ticker.fast_info
        price = round(info.last_price, 2) if info.last_price else None
        prev  = round(info.previous_close, 2) if info.previous_close else None
        if price and prev and prev != 0:
            chg_val = round(price - prev, 2)
            chg_pct = round((chg_val / prev) * 100, 2)
            up = chg_val >= 0
            chg_str = f"+{chg_pct}%" if up else f"{chg_pct}%"
            return {
                "price": f"{price:,.2f}",
                "chg":   chg_str,
                "up":    up,
                "chg_raw": chg_pct,
            }
    except Exception as e:
        print(f"  Error fetching {symbol_yf}: {e}")
    return {"price": "—", "chg": "—", "up": True, "chg_raw": 0}


def refresh_cache():
    """Fetch all quotes and update the cache."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Refreshing quotes from Yahoo Finance...")

    stocks_data = []
    for s in INDIAN_STOCKS:
        q = fetch_quote(s["yf"])
        stocks_data.append({
            "sym":  s["sym"],
            "name": s["name"],
            "price": q["price"],
            "chg":   q["chg"],
            "up":    q["up"],
        })
        print(f"  {s['sym']:12} ₹{q['price']:>12}  {q['chg']}")

    indices_data = []
    for idx in INDICES:
        q = fetch_quote(idx["yf"])
        indices_data.append({
            "sym":  idx["sym"],
            "name": idx["name"],
            "price": q["price"],
            "chg":   q["chg"],
            "up":    q["up"],
        })
        print(f"  {idx['sym']:12}  {q['price']:>12}  {q['chg']}")

    with _cache_lock:
        _cache["stocks"]       = stocks_data
        _cache["indices"]      = indices_data
        _cache["last_updated"] = datetime.now().isoformat()

    print(f"  ✓ Cache updated at {_cache['last_updated']}\n")


def background_refresher():
    """Background thread: refresh cache every CACHE_TTL seconds + self-ping to stay awake."""
    import urllib.request
    self_ping_interval = 8 * 60  # ping self every 8 min to prevent Railway sleep
    last_ping = 0
    while True:
        try:
            refresh_cache()
        except Exception as e:
            print(f"Background refresh error: {e}")
        # Self-ping to keep Railway alive
        now = time.time()
        if now - last_ping > self_ping_interval:
            try:
                port = int(os.environ.get("PORT", 5000))
                url  = f"http://localhost:{port}/api/status"
                urllib.request.urlopen(url, timeout=5)
                last_ping = now
                print("[keep-alive] self-ping ok")
            except Exception as pe:
                print(f"[keep-alive] ping failed: {pe}")
        time.sleep(CACHE_TTL)


# ── API Routes ──

@app.route("/api/stocks")
def api_stocks():
    """Returns top Indian stocks with live price + change."""
    with _cache_lock:
        return jsonify({
            "data": _cache["stocks"],
            "last_updated": _cache["last_updated"],
            "source": "Yahoo Finance (NSE)"
        })


@app.route("/api/indices")
def api_indices():
    """Returns major indices (Nifty, Sensex, BTC, Gold)."""
    with _cache_lock:
        return jsonify({
            "data": _cache["indices"],
            "last_updated": _cache["last_updated"],
            "source": "Yahoo Finance"
        })


@app.route("/api/all")
def api_all():
    """Returns both stocks and indices in one call."""
    with _cache_lock:
        return jsonify({
            "stocks":       _cache["stocks"],
            "indices":      _cache["indices"],
            "last_updated": _cache["last_updated"],
            "source":       "Yahoo Finance"
        })


@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    """Returns a single stock quote. 
    Use NSE symbol e.g. /api/quote/RELIANCE or /api/quote/TCS
    Appends .NS automatically if no suffix given.
    """
    yf_sym = symbol.upper()
    if "." not in yf_sym:
        yf_sym += ".NS"
    q = fetch_quote(yf_sym)
    return jsonify({"symbol": symbol.upper(), **q})


@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "running",
        "last_updated": _cache["last_updated"],
        "cached_stocks": len(_cache["stocks"]),
        "cache_ttl_seconds": CACHE_TTL
    })


@app.route("/")
def index():
    return """
    <h2 style="font-family:monospace">MarketPit API Server 🟢</h2>
    <p style="font-family:monospace">Available endpoints:</p>
    <ul style="font-family:monospace">
      <li><a href="/api/all">/api/all</a> — All stocks + indices</li>
      <li><a href="/api/stocks">/api/stocks</a> — Indian stocks only</li>
      <li><a href="/api/indices">/api/indices</a> — Indices + crypto</li>
      <li><a href="/api/quote/RELIANCE">/api/quote/RELIANCE</a> — Single quote</li>
      <li><a href="/api/status">/api/status</a> — Server status</li>
    </ul>
    <p style="font-family:monospace;color:green">Open marketpit.html in your browser to see the live site.</p>
    """


@app.route("/api/ai", methods=["POST"])
def api_ai():
    """Proxy requests to Anthropic API to avoid CORS issues."""
    if req_lib is None:
        return jsonify({"error": "requests library not installed"}), 500

    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "No JSON body"}), 400

        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            return jsonify({"error": "ANTHROPIC_API_KEY not set on server"}), 500

        resp = req_lib.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
            },
            json=body,
            timeout=30,
        )
        return jsonify(resp.json()), resp.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Start ──
if __name__ == "__main__":
    print("=" * 50)
    print("  MarketPit Backend Server")
    print("  Fetching Indian stock data from Yahoo Finance")
    print("=" * 50)

    # Initial fetch before accepting requests
    refresh_cache()

    # Start background refresh thread
    t = threading.Thread(target=background_refresher, daemon=True)
    t.start()

    print("Server running at http://localhost:5000")
    print("Open marketpit.html in your browser\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
