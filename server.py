"""
MarketPit — Python Backend Server
Fetches real-time Indian stock data from Yahoo Finance (yfinance),
FII/DII data from NSE India, and Earnings calendar from NSE.

Run:  python server.py
Then open marketpit.html in your browser.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import threading
import time
import os
import json

try:
    import requests as req_lib
except ImportError:
    req_lib = None

app = Flask(__name__)
CORS(app)

# ── Indian Stock Symbols (NSE via Yahoo Finance) ──
INDIAN_STOCKS = [
    # Banking
    {"sym": "HDFCBANK",   "yf": "HDFCBANK.NS",    "name": "HDFC Bank"},
    {"sym": "SBIN",       "yf": "SBIN.NS",         "name": "State Bank of India"},
    {"sym": "ICICIBANK",  "yf": "ICICIBANK.NS",    "name": "ICICI Bank"},
    {"sym": "AXISBANK",   "yf": "AXISBANK.NS",     "name": "Axis Bank"},
    {"sym": "KOTAKBANK",  "yf": "KOTAKBANK.NS",    "name": "Kotak Mahindra Bank"},
    {"sym": "INDUSINDBK", "yf": "INDUSINDBK.NS",   "name": "IndusInd Bank"},
    # IT
    {"sym": "TCS",        "yf": "TCS.NS",          "name": "Tata Consultancy"},
    {"sym": "INFY",       "yf": "INFY.NS",         "name": "Infosys"},
    {"sym": "WIPRO",      "yf": "WIPRO.NS",        "name": "Wipro Ltd"},
    {"sym": "HCLTECH",    "yf": "HCLTECH.NS",      "name": "HCL Technologies"},
    {"sym": "TECHM",      "yf": "TECHM.NS",        "name": "Tech Mahindra"},
    {"sym": "LTIM",       "yf": "LTIM.NS",         "name": "LTIMindtree"},
    # Auto
    {"sym": "TATAMOTORS", "yf": "TATAMOTORS.NS",   "name": "Tata Motors"},
    {"sym": "MARUTI",     "yf": "MARUTI.NS",       "name": "Maruti Suzuki"},
    {"sym": "M&M",        "yf": "M%26M.NS",        "name": "Mahindra & Mahindra"},
    {"sym": "HEROMOTOCO", "yf": "HEROMOTOCO.NS",   "name": "Hero MotoCorp"},
    {"sym": "EICHERMOT",  "yf": "EICHERMOT.NS",    "name": "Eicher Motors"},
    # Pharma
    {"sym": "SUNPHARMA",  "yf": "SUNPHARMA.NS",    "name": "Sun Pharmaceutical"},
    {"sym": "DRREDDY",    "yf": "DRREDDY.NS",      "name": "Dr. Reddy's Labs"},
    {"sym": "CIPLA",      "yf": "CIPLA.NS",        "name": "Cipla"},
    {"sym": "DIVISLAB",   "yf": "DIVISLAB.NS",     "name": "Divi's Laboratories"},
    {"sym": "APOLLOHOSP", "yf": "APOLLOHOSP.NS",   "name": "Apollo Hospitals"},
    # Energy
    {"sym": "RELIANCE",   "yf": "RELIANCE.NS",     "name": "Reliance Industries"},
    {"sym": "ONGC",       "yf": "ONGC.NS",         "name": "ONGC"},
    {"sym": "BPCL",       "yf": "BPCL.NS",         "name": "BPCL"},
    {"sym": "IOC",        "yf": "IOC.NS",          "name": "Indian Oil Corp"},
    {"sym": "NTPC",       "yf": "NTPC.NS",         "name": "NTPC"},
    # Metals
    {"sym": "TATASTEEL",  "yf": "TATASTEEL.NS",    "name": "Tata Steel"},
    {"sym": "JSWSTEEL",   "yf": "JSWSTEEL.NS",     "name": "JSW Steel"},
    {"sym": "HINDALCO",   "yf": "HINDALCO.NS",     "name": "Hindalco"},
    {"sym": "COALINDIA",  "yf": "COALINDIA.NS",    "name": "Coal India"},
    # FMCG
    {"sym": "NESTLEIND",  "yf": "NESTLEIND.NS",    "name": "Nestle India"},
    {"sym": "BRITANNIA",  "yf": "BRITANNIA.NS",    "name": "Britannia"},
    {"sym": "ITC",        "yf": "ITC.NS",          "name": "ITC Ltd"},
    {"sym": "HINDUNILVR", "yf": "HINDUNILVR.NS",   "name": "Hindustan Unilever"},
    # Infra / Utilities
    {"sym": "LT",         "yf": "LT.NS",           "name": "Larsen & Toubro"},
    {"sym": "POWERGRID",  "yf": "POWERGRID.NS",    "name": "Power Grid Corp"},
    {"sym": "ADANIENT",   "yf": "ADANIENT.NS",     "name": "Adani Enterprises"},
    {"sym": "ULTRACEMCO", "yf": "ULTRACEMCO.NS",   "name": "UltraTech Cement"},
    # Finance / Consumer
    {"sym": "BAJFINANCE", "yf": "BAJFINANCE.NS",   "name": "Bajaj Finance"},
    {"sym": "BAJAJFINSV", "yf": "BAJAJFINSV.NS",   "name": "Bajaj Finserv"},
    {"sym": "TITAN",      "yf": "TITAN.NS",        "name": "Titan Company"},
    {"sym": "ASIANPAINT", "yf": "ASIANPAINT.NS",   "name": "Asian Paints"},
    {"sym": "DMART",      "yf": "DMART.NS",        "name": "DMart"},
    {"sym": "JUBLFOOD",   "yf": "JUBLFOOD.NS",     "name": "Jubilant Foodworks"},
]

# ── Index Symbols ──
INDICES = [
    {"sym": "NIFTY 50",   "yf": "^NSEI",   "name": "Nifty 50"},
    {"sym": "SENSEX",     "yf": "^BSESN",  "name": "BSE Sensex"},
    {"sym": "NIFTY BANK", "yf": "^NSEBANK","name": "Nifty Bank"},
    {"sym": "BTC-USD",    "yf": "BTC-USD", "name": "Bitcoin"},
    {"sym": "ETH-USD",    "yf": "ETH-USD", "name": "Ethereum"},
    {"sym": "GOLD",       "yf": "GC=F",    "name": "Gold"},
    {"sym": "SILVER",     "yf": "SI=F",    "name": "Silver"},
    {"sym": "CRUDE",      "yf": "CL=F",    "name": "Crude Oil WTI"},
    {"sym": "BRENT",      "yf": "BZ=F",    "name": "Brent Crude"},
    {"sym": "NATURALGAS", "yf": "NG=F",    "name": "Natural Gas"},
    {"sym": "COPPER",     "yf": "HG=F",    "name": "Copper"},
    {"sym": "PLATINUM",   "yf": "PL=F",    "name": "Platinum"},
    {"sym": "WHEAT",      "yf": "ZW=F",    "name": "Wheat"},
    {"sym": "CORN",       "yf": "ZC=F",    "name": "Corn"},
]

# ── Cache ──
_cache = {"stocks": [], "indices": [], "last_updated": None}
_cache_lock = threading.Lock()
CACHE_TTL = 30  # seconds — refresh every 30s

# ── FII/DII Cache ──
_fii_cache = {"data": [], "last_updated": None}
_fii_lock  = threading.Lock()
FII_CACHE_TTL = 60 * 60  # refresh every 1 hour

# ── Earnings Cache ──
_earnings_cache = {"data": [], "last_updated": None}
_earnings_lock  = threading.Lock()
EARNINGS_CACHE_TTL = 60 * 60 * 6  # refresh every 6 hours

# ── NSE request headers (required to avoid 403) ──
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}


# ════════════════════════════════════════════════════════
#  STOCK QUOTE HELPERS
# ════════════════════════════════════════════════════════

def fetch_quote(symbol_yf):
    """Fetch latest quote for a single Yahoo Finance symbol."""
    try:
        ticker = yf.Ticker(symbol_yf)
        info   = ticker.fast_info
        price  = round(info.last_price, 2) if info.last_price else None
        prev   = round(info.previous_close, 2) if info.previous_close else None
        if price and prev and prev != 0:
            chg_val = round(price - prev, 2)
            chg_pct = round((chg_val / prev) * 100, 2)
            up      = chg_val >= 0
            chg_str = f"+{chg_pct}%" if up else f"{chg_pct}%"
            return {"price": price, "chg": chg_str, "up": up, "chg_raw": chg_pct}  # price as float
    except Exception as e:
        print(f"  Error fetching {symbol_yf}: {e}")
    return {"price": "—", "chg": "—", "up": True, "chg_raw": 0}


def refresh_cache():
    """Fetch all stock/index quotes in parallel and update cache."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Refreshing quotes (parallel)...")

    def fetch_one(s):
        q = fetch_quote(s["yf"])
        return {"sym": s["sym"], "name": s["name"],
                "price": q["price"], "chg": q["chg"], "up": q["up"]}

    stocks_data = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(fetch_one, s): s for s in INDIAN_STOCKS}
        for f in as_completed(futures):
            try:
                stocks_data.append(f.result())
            except Exception as e:
                print(f"  Stock fetch error: {e}")

    order = {s["sym"]: i for i, s in enumerate(INDIAN_STOCKS)}
    stocks_data.sort(key=lambda x: order.get(x["sym"], 999))

    indices_data = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fetch_one, idx): idx for idx in INDICES}
        for f in as_completed(futures):
            try:
                indices_data.append(f.result())
            except Exception as e:
                print(f"  Index fetch error: {e}")

    with _cache_lock:
        _cache["stocks"]       = stocks_data
        _cache["indices"]      = indices_data
        _cache["last_updated"] = datetime.now().isoformat()
    print(f"  ✓ {len(stocks_data)} stocks + {len(indices_data)} indices updated\n")


# ════════════════════════════════════════════════════════
#  FII / DII  —  NSE India
# ════════════════════════════════════════════════════════

def fetch_fii_from_nse():
    """
    Fetch FII/DII cash market data.
    Tries multiple sources: NSE India direct, then alternative endpoints.
    Returns list of {date, fii_net, dii_net} for last 30 trading days.
    """
    if req_lib is None:
        print("  [FII] requests library not available")
        return []

    # ── Attempt 1: NSE India with full session setup ──
    for attempt in range(2):
        try:
            session = req_lib.Session()
            # Warm up cookies with two requests (NSE requires this)
            session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=12)
            time.sleep(1)
            session.get("https://www.nseindia.com/market-data/fii-dii-trading-activity",
                        headers=NSE_HEADERS, timeout=10)
            time.sleep(0.5)

            url  = "https://www.nseindia.com/api/fiidiiTradeReact"
            resp = session.get(url, headers={**NSE_HEADERS,
                "X-Requested-With": "XMLHttpRequest"}, timeout=15)

            if resp.status_code == 200:
                raw     = resp.json()
                results = []
                for row in raw:
                    try:
                        date_str = row.get("date", "")
                        fii_buy  = float(str(row.get("fiiBuy",  "0")).replace(",", "") or 0)
                        fii_sell = float(str(row.get("fiiSell", "0")).replace(",", "") or 0)
                        dii_buy  = float(str(row.get("diiBuy",  "0")).replace(",", "") or 0)
                        dii_sell = float(str(row.get("diiSell", "0")).replace(",", "") or 0)
                        fii_net  = round(fii_buy - fii_sell, 2)
                        dii_net  = round(dii_buy - dii_sell, 2)
                        try:
                            dt       = datetime.strptime(date_str, "%d-%b-%Y")
                            date_fmt = dt.strftime("%d %b")
                        except Exception:
                            date_fmt = date_str
                        if abs(fii_net) > 1 or abs(dii_net) > 1:   # skip zero-data rows
                            results.append({
                                "date": date_fmt, "fii_net": fii_net,
                                "dii_net": dii_net,
                                "net": round(fii_net + dii_net, 2),
                            })
                    except Exception:
                        continue
                if results:
                    print(f"  [FII] ✓ NSE: {len(results)} days fetched")
                    return results[:30]
            else:
                print(f"  [FII] NSE attempt {attempt+1}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  [FII] NSE attempt {attempt+1} error: {e}")
        time.sleep(2)

    # ── Attempt 2: Stooq / alternative public source ──
    try:
        # Use yfinance to approximate FII sentiment via Nifty volume / advance-decline
        # This is a best-effort fallback — returns empty to preserve frontend static data
        print("  [FII] All NSE attempts failed — frontend will use static fallback data")
        return []
    except Exception as e:
        print(f"  [FII] Fallback error: {e}")
        return []


def refresh_fii():
    """Refresh FII/DII cache from NSE."""
    data = fetch_fii_from_nse()
    if data:
        with _fii_lock:
            _fii_cache["data"]         = data
            _fii_cache["last_updated"] = datetime.now().isoformat()


# ════════════════════════════════════════════════════════
#  EARNINGS CALENDAR  —  NSE India
# ════════════════════════════════════════════════════════

# Map of NSE symbols → readable names for enrichment
COMPANY_NAMES = {
    "TCS": "Tata Consultancy", "INFY": "Infosys", "HDFCBANK": "HDFC Bank",
    "RELIANCE": "Reliance Industries", "WIPRO": "Wipro", "ICICIBANK": "ICICI Bank",
    "SBIN": "State Bank of India", "BAJFINANCE": "Bajaj Finance",
    "HCLTECH": "HCL Technologies", "TATAMOTORS": "Tata Motors",
    "AXISBANK": "Axis Bank", "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen & Toubro", "MARUTI": "Maruti Suzuki",
    "SUNPHARMA": "Sun Pharmaceutical", "TITAN": "Titan Company",
    "NESTLEIND": "Nestle India", "ULTRACEMCO": "UltraTech Cement",
    "ASIANPAINT": "Asian Paints", "TECHM": "Tech Mahindra",
    "POWERGRID": "Power Grid Corp", "NTPC": "NTPC Limited",
    "ONGC": "Oil & Natural Gas", "COALINDIA": "Coal India",
    "JSWSTEEL": "JSW Steel", "TATASTEEL": "Tata Steel",
    "DRREDDY": "Dr. Reddy's Labs", "CIPLA": "Cipla",
    "HEROMOTOCO": "Hero MotoCorp", "ADANIENT": "Adani Enterprises",
    "BHARTIARTL": "Bharti Airtel", "INDUSINDBK": "IndusInd Bank",
    "M&M": "Mahindra & Mahindra", "DIVISLAB": "Divi's Laboratories",
    "BRITANNIA": "Britannia Industries", "EICHERMOT": "Eicher Motors",
    "GRASIM": "Grasim Industries", "APOLLOHOSP": "Apollo Hospitals",
    "BAJAJ-AUTO": "Bajaj Auto", "BPCL": "BPCL",
    "HINDALCO": "Hindalco Industries", "TATACONSUM": "Tata Consumer",
    "UPL": "UPL Limited", "SHREECEM": "Shree Cement",
    "VEDL": "Vedanta", "BANKBARODA": "Bank of Baroda",
}

# Sector mapping
SECTOR_MAP = {
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT", "TECHM": "IT",
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "SBIN": "Banking",
    "AXISBANK": "Banking", "KOTAKBANK": "Banking", "INDUSINDBK": "Banking",
    "BANKBARODA": "Banking", "RELIANCE": "Energy", "ONGC": "Energy",
    "BPCL": "Energy", "NTPC": "Energy", "POWERGRID": "Utilities",
    "BAJFINANCE": "Finance", "TATAMOTORS": "Auto", "MARUTI": "Auto",
    "HEROMOTOCO": "Auto", "EICHERMOT": "Auto", "BAJAJ-AUTO": "Auto",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma",
    "DIVISLAB": "Pharma", "LT": "Infra", "ADANIENT": "Conglomerate",
    "TITAN": "Consumer", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG",
    "TATACONSUM": "FMCG", "ASIANPAINT": "Consumer", "BHARTIARTL": "Telecom",
    "JSWSTEEL": "Metal", "TATASTEEL": "Metal", "HINDALCO": "Metal",
    "VEDL": "Metal", "ULTRACEMCO": "Cement", "SHREECEM": "Cement",
    "GRASIM": "Conglomerate", "M&M": "Auto", "APOLLOHOSP": "Healthcare",
    "COALINDIA": "Mining", "UPL": "Chemicals",
}


def fetch_earnings_from_nse():
    """
    Fetch upcoming board meetings (earnings results) from NSE.
    Returns a list of {sym, name, date, sector, note, type}.
    """
    if req_lib is None:
        print("  [EARNINGS] requests library not available")
        return []

    results = []

    try:
        session = req_lib.Session()
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=10)

        # Fetch board meetings for next 3 months
        today = datetime.now()
        from_date = today.strftime("%d-%m-%Y")
        to_date   = (today + timedelta(days=90)).strftime("%d-%m-%Y")
        url = f"https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date={from_date}&to_date={to_date}"

        resp = session.get(url, headers=NSE_HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  [EARNINGS] NSE board meetings returned {resp.status_code}")
        else:
            data = resp.json()
            for row in data:
                try:
                    sym     = row.get("symbol", "").upper()
                    purpose = row.get("purpose", "").lower()
                    date_str= row.get("bm_date", "") or row.get("date", "")

                    # Only include quarterly results meetings
                    if not any(k in purpose for k in ["quarterly", "financial result", "q1", "q2", "q3", "q4", "annual"]):
                        continue

                    try:
                        dt       = datetime.strptime(date_str, "%d-%b-%Y")
                        date_iso = dt.strftime("%Y-%m-%d")
                    except Exception:
                        try:
                            dt       = datetime.strptime(date_str, "%d-%m-%Y")
                            date_iso = dt.strftime("%Y-%m-%d")
                        except Exception:
                            continue

                    name   = COMPANY_NAMES.get(sym, row.get("sm_name", sym))
                    sector = SECTOR_MAP.get(sym, "Equity")
                    note   = row.get("purpose", "Quarterly Results")

                    results.append({
                        "type":   "results",
                        "sym":    sym,
                        "name":   name,
                        "date":   date_iso,
                        "sector": sector,
                        "note":   note,
                        "est":    None,
                        "act":    None,
                        "beat":   None,
                    })
                except Exception as row_err:
                    print(f"  [EARNINGS] Row error: {row_err}")
                    continue

        print(f"  [EARNINGS] ✓ Found {len(results)} upcoming earnings from NSE board meetings")

    except Exception as e:
        print(f"  [EARNINGS] Board meetings fetch error: {e}")

    # ── Also fetch dividends ──
    try:
        session2 = req_lib.Session()
        session2.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=10)

        today    = datetime.now()
        from_d   = today.strftime("%d-%m-%Y")
        to_d     = (today + timedelta(days=60)).strftime("%d-%m-%Y")
        div_url  = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_d}&to_date={to_d}"
        resp2    = session2.get(div_url, headers=NSE_HEADERS, timeout=15)

        if resp2.status_code == 200:
            div_data = resp2.json()
            div_count = 0
            for row in div_data:
                try:
                    action = str(row.get("subject", "")).lower()
                    if "dividend" not in action:
                        continue
                    sym      = row.get("symbol", "").upper()
                    ex_date  = row.get("exDate", "") or row.get("ex_date", "")
                    try:
                        dt       = datetime.strptime(ex_date, "%d-%b-%Y")
                        date_iso = dt.strftime("%Y-%m-%d")
                    except Exception:
                        continue

                    amount_str = row.get("subject", "Dividend")
                    name       = COMPANY_NAMES.get(sym, row.get("comp", sym))
                    sector     = SECTOR_MAP.get(sym, "Equity")

                    results.append({
                        "type":    "dividend",
                        "sym":     sym,
                        "name":    name,
                        "date":    date_iso,
                        "sector":  sector,
                        "note":    amount_str,
                        "amount":  amount_str,
                        "exDate":  date_iso,
                    })
                    div_count += 1
                except Exception:
                    continue
            print(f"  [EARNINGS] ✓ Found {div_count} upcoming dividends from NSE")

    except Exception as e:
        print(f"  [EARNINGS] Dividends fetch error: {e}")

    # Sort by date
    results.sort(key=lambda x: x.get("date", ""))
    return results


def refresh_earnings():
    """Refresh earnings/events cache from NSE."""
    data = fetch_earnings_from_nse()
    if data:
        with _earnings_lock:
            _earnings_cache["data"]         = data
            _earnings_cache["last_updated"] = datetime.now().isoformat()


# ════════════════════════════════════════════════════════
#  BACKGROUND REFRESH THREAD
# ════════════════════════════════════════════════════════

def background_refresher():
    """Background thread: refresh stocks every 60s, FII/Earnings hourly."""
    import urllib.request
    self_ping_interval = 8 * 60
    last_ping          = 0
    last_fii_refresh   = 0
    last_earn_refresh  = 0

    while True:
        try:
            refresh_cache()
        except Exception as e:
            print(f"Background stock refresh error: {e}")

        now = time.time()

        # Refresh FII every hour
        if now - last_fii_refresh > FII_CACHE_TTL:
            try:
                refresh_fii()
                last_fii_refresh = time.time()
            except Exception as e:
                print(f"FII refresh error: {e}")

        # Refresh earnings every 6 hours
        if now - last_earn_refresh > EARNINGS_CACHE_TTL:
            try:
                refresh_earnings()
                last_earn_refresh = time.time()
            except Exception as e:
                print(f"Earnings refresh error: {e}")

        # Self-ping to keep Railway alive
        if now - last_ping > self_ping_interval:
            try:
                port = int(os.environ.get("PORT", 5000))
                url  = f"http://localhost:{port}/api/status"
                urllib.request.urlopen(url, timeout=5)
                last_ping = time.time()
                print("[keep-alive] self-ping ok")
            except Exception as pe:
                print(f"[keep-alive] ping failed: {pe}")

        time.sleep(CACHE_TTL)


# ════════════════════════════════════════════════════════
#  API ROUTES
# ════════════════════════════════════════════════════════

@app.route("/api/stocks")
def api_stocks():
    with _cache_lock:
        return jsonify({"data": _cache["stocks"], "last_updated": _cache["last_updated"], "source": "Yahoo Finance (NSE)"})


@app.route("/api/indices")
def api_indices():
    with _cache_lock:
        return jsonify({"data": _cache["indices"], "last_updated": _cache["last_updated"], "source": "Yahoo Finance"})


@app.route("/api/all")
def api_all():
    with _cache_lock:
        stocks  = _cache["stocks"]
        indices = _cache["indices"]
        last_up = _cache["last_updated"]
    # Split indices into actual indices vs commodities/crypto for frontend convenience
    index_syms = {"NIFTY 50", "SENSEX", "NIFTY BANK"}
    actual_indices = [i for i in indices if i["sym"] in index_syms]
    commodities    = [i for i in indices if i["sym"] not in index_syms]
    return jsonify({
        "stocks": stocks,
        "indices": actual_indices,
        "commodities": commodities,   # ← Gold, Silver, Crude, BTC, ETH etc.
        "last_updated": last_up,
        "source": "Yahoo Finance"
    })


# Commodity symbol map for /api/quote
COMMODITY_YF_MAP = {
    "GOLD": "GC=F", "SILVER": "SI=F", "CRUDE": "CL=F", "BRENT": "BZ=F",
    "NATURALGAS": "NG=F", "COPPER": "HG=F", "PLATINUM": "PL=F",
    "WHEAT": "ZW=F", "CORN": "ZC=F",
}
CRYPTO_YF_MAP = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "BNB": "BNB-USD",
    "SOL": "SOL-USD", "XRP": "XRP-USD", "DOGE": "DOGE-USD",
    "ADA": "ADA-USD", "MATIC": "MATIC-USD", "DOT": "DOT-USD",
    "AVAX": "AVAX-USD", "LTC": "LTC-USD", "LINK": "LINK-USD",
}

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    sym_upper = symbol.upper()
    # Check commodity first
    if sym_upper in COMMODITY_YF_MAP:
        yf_sym = COMMODITY_YF_MAP[sym_upper]
    # Check crypto
    elif sym_upper in CRYPTO_YF_MAP:
        yf_sym = CRYPTO_YF_MAP[sym_upper]
    # NSE stock
    elif "." not in sym_upper:
        yf_sym = sym_upper + ".NS"
    else:
        yf_sym = sym_upper
    q = fetch_quote(yf_sym)
    return jsonify({"symbol": sym_upper, **q})


STATIC_FII_FALLBACK = [
    {"date": "13 Mar", "fii_net": -1876.43, "dii_net": 2943.21, "net":  1066.78},
    {"date": "12 Mar", "fii_net": -2341.67, "dii_net": 3187.89, "net":   846.22},
    {"date": "11 Mar", "fii_net": -4823.56, "dii_net": 3912.44, "net":  -911.12},
    {"date": "10 Mar", "fii_net": -3567.89, "dii_net": 5021.34, "net":  1453.45},
    {"date": "07 Mar", "fii_net": -2134.23, "dii_net": 4312.67, "net":  2178.44},
    {"date": "06 Mar", "fii_net": -1876.54, "dii_net": 3456.78, "net":  1580.24},
    {"date": "05 Mar", "fii_net": -3234.67, "dii_net": 5678.90, "net":  2444.23},
    {"date": "04 Mar", "fii_net": -6543.21, "dii_net": 9876.54, "net":  3333.33},
    {"date": "03 Mar", "fii_net": -4123.45, "dii_net": 7234.56, "net":  3111.11},
    {"date": "02 Mar", "fii_net": -2456.78, "dii_net": 6789.01, "net":  4332.23},
    {"date": "28 Feb", "fii_net": -3123.45, "dii_net": 5234.56, "net":  2111.11},
    {"date": "27 Feb", "fii_net": -4234.56, "dii_net": 6345.67, "net":  2111.11},
    {"date": "26 Feb", "fii_net": -2876.54, "dii_net": 4123.45, "net":  1246.91},
    {"date": "25 Feb", "fii_net": -4876.54, "dii_net": 6543.21, "net":  1666.67},
    {"date": "24 Feb", "fii_net": -5987.65, "dii_net": 7654.32, "net":  1666.67},
]

@app.route("/api/fii")
def api_fii():
    """
    Returns FII/DII cash market net activity for the last 30 trading days.
    Data source: NSE India (refreshed every hour). Falls back to static data.
    Format: [{date, fii_net, dii_net, net}, ...]
    """
    with _fii_lock:
        data         = _fii_cache["data"]
        last_updated = _fii_cache["last_updated"]

    if not data:
        # On-demand fetch if cache is empty
        data = fetch_fii_from_nse()
        if data:
            with _fii_lock:
                _fii_cache["data"]         = data
                _fii_cache["last_updated"] = datetime.now().isoformat()
            last_updated = _fii_cache["last_updated"]

    # Always return something — use static fallback if NSE blocked
    final_data = data if data else STATIC_FII_FALLBACK
    source = "NSE India" if data else "Static (NSE unavailable)"

    return jsonify({
        "data":         final_data,
        "last_updated": last_updated or datetime.now().isoformat(),
        "source":       source,
        "count":        len(final_data),
    })


@app.route("/api/earnings")
def api_earnings():
    """
    Returns upcoming quarterly results, dividends, and board meetings.
    Data source: NSE India corporate actions (refreshed every 6 hours).
    Format: [{type, sym, name, date, sector, note, ...}, ...]
    """
    with _earnings_lock:
        data         = _earnings_cache["data"]
        last_updated = _earnings_cache["last_updated"]

    if not data:
        # On-demand fetch if cache is empty
        data = fetch_earnings_from_nse()
        if data:
            with _earnings_lock:
                _earnings_cache["data"]         = data
                _earnings_cache["last_updated"] = datetime.now().isoformat()
            last_updated = _earnings_cache["last_updated"]

    return jsonify({
        "data":         data,
        "last_updated": last_updated,
        "source":       "NSE India Corporate Actions",
        "count":        len(data),
    })


@app.route("/api/nifty-spot")
def api_nifty_spot():
    """Returns live Nifty 50 and Bank Nifty spot prices."""
    with _cache_lock:
        indices = _cache.get("indices", [])
    nifty  = next((i for i in indices if "NIFTY 50"   in i["sym"]), None)
    bank   = next((i for i in indices if "NIFTY BANK" in i["sym"]), None)
    return jsonify({
        "nifty":  {"price": nifty["price"] if nifty else "—", "chg": nifty["chg"] if nifty else "—"},
        "bank":   {"price": bank["price"]  if bank  else "—", "chg": bank["chg"]  if bank  else "—"},
        "source": "Yahoo Finance",
        "last_updated": _cache.get("last_updated"),
    })



    with _fii_lock:
        fii_updated = _fii_cache["last_updated"]
        fii_count   = len(_fii_cache["data"])
    with _earnings_lock:
        earn_updated = _earnings_cache["last_updated"]
        earn_count   = len(_earnings_cache["data"])
    return jsonify({
        "status":              "running",
        "last_updated":        _cache["last_updated"],
        "cached_stocks":       len(_cache["stocks"]),
        "cache_ttl_seconds":   CACHE_TTL,
        "fii_last_updated":    fii_updated,
        "fii_days_cached":     fii_count,
        "earnings_last_updated": earn_updated,
        "earnings_count":      earn_count,
    })


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
            headers={"Content-Type": "application/json", "x-api-key": anthropic_key,
                     "anthropic-version": "2023-06-01"},
            json=body, timeout=30,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
      <li><a href="/api/fii">/api/fii</a> — FII/DII live data (NSE India)</li>
      <li><a href="/api/earnings">/api/earnings</a> — Earnings calendar (NSE India)</li>
      <li><a href="/api/status">/api/status</a> — Server status</li>
    </ul>
    """


# ════════════════════════════════════════════════════════
#  START
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  MarketPit Backend Server")
    print("  Stocks: Yahoo Finance | FII+Earnings: NSE India")
    print("=" * 55)

    # Initial fetches before accepting requests
    refresh_cache()

    print("Fetching FII/DII data from NSE India...")
    refresh_fii()

    print("Fetching Earnings calendar from NSE India...")
    refresh_earnings()

    # Start background refresh thread
    t = threading.Thread(target=background_refresher, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 5000))
    print(f"\nServer running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
