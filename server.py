"""
MarketPit — Python Backend Server (Nifty 500 Edition)
Fetches real-time Indian stock data from Yahoo Finance (yfinance)

Run:  py server.py
Then open marketpit.html in your browser.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

# ── All Nifty 500 Stocks (NSE symbols) ──
NIFTY500 = [
    ("RELIANCE",    "Reliance Industries"),
    ("TCS",         "Tata Consultancy Services"),
    ("HDFCBANK",    "HDFC Bank"),
    ("BHARTIARTL",  "Bharti Airtel"),
    ("ICICIBANK",   "ICICI Bank"),
    ("INFOSYS",     "Infosys"),
    ("SBIN",        "State Bank of India"),
    ("HINDUNILVR",  "Hindustan Unilever"),
    ("ITC",         "ITC Ltd"),
    ("LT",          "Larsen & Toubro"),
    ("BAJFINANCE",  "Bajaj Finance"),
    ("HCLTECH",     "HCL Technologies"),
    ("MARUTI",      "Maruti Suzuki"),
    ("SUNPHARMA",   "Sun Pharmaceutical"),
    ("ADANIENT",    "Adani Enterprises"),
    ("KOTAKBANK",   "Kotak Mahindra Bank"),
    ("AXISBANK",    "Axis Bank"),
    ("WIPRO",       "Wipro Ltd"),
    ("ULTRACEMCO",  "UltraTech Cement"),
    ("TITAN",       "Titan Company"),
    ("ASIANPAINT",  "Asian Paints"),
    ("NESTLEIND",   "Nestle India"),
    ("POWERGRID",   "Power Grid Corp"),
    ("NTPC",        "NTPC Ltd"),
    ("TATAMOTORS",  "Tata Motors"),
    ("TECHM",       "Tech Mahindra"),
    ("INDUSINDBK",  "IndusInd Bank"),
    ("BAJAJFINSV",  "Bajaj Finserv"),
    ("JSWSTEEL",    "JSW Steel"),
    ("TATASTEEL",   "Tata Steel"),
    ("COALINDIA",   "Coal India"),
    ("ONGC",        "ONGC"),
    ("ADANIPORTS",  "Adani Ports"),
    ("GRASIM",      "Grasim Industries"),
    ("BRITANNIA",   "Britannia Industries"),
    ("CIPLA",       "Cipla Ltd"),
    ("DRREDDY",     "Dr Reddy's Labs"),
    ("HEROMOTOCO",  "Hero MotoCorp"),
    ("HINDALCO",    "Hindalco Industries"),
    ("DIVISLAB",    "Divi's Laboratories"),
    ("EICHERMOT",   "Eicher Motors"),
    ("BPCL",        "Bharat Petroleum"),
    ("TATACONSUM",  "Tata Consumer Products"),
    ("APOLLOHOSP",  "Apollo Hospitals"),
    ("BAJAJ-AUTO",  "Bajaj Auto"),
    ("VEDL",        "Vedanta Ltd"),
    ("SBILIFE",     "SBI Life Insurance"),
    ("HDFCLIFE",    "HDFC Life Insurance"),
    ("ICICIPRULI",  "ICICI Prudential Life"),
    ("SHREECEM",    "Shree Cement"),
    ("AMBUJACEM",   "Ambuja Cements"),
    ("ACC",         "ACC Ltd"),
    ("SIEMENS",     "Siemens India"),
    ("HAVELLS",     "Havells India"),
    ("DABUR",       "Dabur India"),
    ("MARICO",      "Marico Ltd"),
    ("PIDILITIND",  "Pidilite Industries"),
    ("BANKBARODA",  "Bank of Baroda"),
    ("PNB",         "Punjab National Bank"),
    ("CANBK",       "Canara Bank"),
    ("UNIONBANK",   "Union Bank of India"),
    ("INDHOTEL",    "Indian Hotels"),
    ("TATAPOWER",   "Tata Power"),
    ("TORNTPHARM",  "Torrent Pharmaceuticals"),
    ("LUPIN",       "Lupin Ltd"),
    ("BIOCON",      "Biocon Ltd"),
    ("AUROPHARMA",  "Aurobindo Pharma"),
    ("IPCALAB",     "IPCA Laboratories"),
    ("ALKEM",       "Alkem Laboratories"),
    ("LALPATHLAB",  "Dr Lal PathLabs"),
    ("METROPOLIS",  "Metropolis Healthcare"),
    ("MAXHEALTH",   "Max Healthcare"),
    ("FORTIS",      "Fortis Healthcare"),
    ("NH",          "Narayana Hrudayalaya"),
    ("ZOMATO",      "Zomato Ltd"),
    ("NYKAA",       "FSN E-Commerce (Nykaa)"),
    ("PAYTM",       "One97 Communications (Paytm)"),
    ("POLICYBZR",   "PB Fintech (PolicyBazaar)"),
    ("DELHIVERY",   "Delhivery Ltd"),
    ("IRCTC",       "IRCTC"),
    ("IRFC",        "Indian Railway Finance"),
    ("RVNL",        "Rail Vikas Nigam"),
    ("HAL",         "Hindustan Aeronautics"),
    ("BEL",         "Bharat Electronics"),
    ("BHEL",        "Bharat Heavy Electricals"),
    ("NMDC",        "NMDC Ltd"),
    ("SAIL",        "Steel Authority of India"),
    ("RECLTD",      "REC Ltd"),
    ("PFC",         "Power Finance Corp"),
    ("NHPC",        "NHPC Ltd"),
    ("SJVN",        "SJVN Ltd"),
    ("TORNTPOWER",  "Torrent Power"),
    ("CESC",        "CESC Ltd"),
    ("ADANIGREEN",  "Adani Green Energy"),
    ("ADANIPOWER",  "Adani Power"),
    ("SUZLON",      "Suzlon Energy"),
    ("IDFCFIRSTB",  "IDFC First Bank"),
    ("FEDERALBNK",  "Federal Bank"),
    ("RBLBANK",     "RBL Bank"),
    ("BANDHANBNK",  "Bandhan Bank"),
    ("AUBANK",      "AU Small Finance Bank"),
    ("CHOLAFIN",    "Cholamandalam Finance"),
    ("SHRIRAMFIN",  "Shriram Finance"),
    ("MUTHOOTFIN",  "Muthoot Finance"),
    ("MANAPPURAM",  "Manappuram Finance"),
    ("IIFL",        "IIFL Finance"),
    ("M&M",         "Mahindra & Mahindra"),
    ("ASHOKLEY",    "Ashok Leyland"),
    ("TVSMOTOR",    "TVS Motor Company"),
    ("BALKRISIND",  "Balkrishna Industries"),
    ("APOLLOTYRE",  "Apollo Tyres"),
    ("MRF",         "MRF Ltd"),
    ("CEATLTD",     "CEAT Ltd"),
    ("MOTHERSON",   "Motherson Sumi Wiring"),
    ("BOSCHLTD",    "Bosch Ltd"),
    ("THERMAX",     "Thermax Ltd"),
    ("ABB",         "ABB India"),
    ("CUMMINSIND",  "Cummins India"),
    ("KALYANKJIL",  "Kalyan Jewellers"),
    ("BATA",        "Bata India"),
    ("RELAXO",      "Relaxo Footwears"),
    ("METROBRAND",  "Metro Brands"),
    ("VBL",         "Varun Beverages"),
    ("JUBLFOOD",    "Jubilant Foodworks"),
    ("DEVYANI",     "Devyani International"),
    ("WESTLIFE",    "Westlife Foodworld"),
    ("IRCTC",       "IRCTC"),
    ("EASEMYTRIP",  "Easy Trip Planners"),
    ("THOMASCOOK",  "Thomas Cook India"),
    ("LEMONTRE",    "Lemon Tree Hotels"),
    ("EIHOTEL",     "EIH Ltd"),
    ("PVRINOX",     "PVR INOX"),
    ("NAZARA",      "Nazara Technologies"),
    ("TATAELXSI",   "Tata Elxsi"),
    ("KPIT",        "KPIT Technologies"),
    ("LTTS",        "L&T Technology Services"),
    ("PERSISTENT",  "Persistent Systems"),
    ("MPHASIS",     "Mphasis Ltd"),
    ("COFORGE",     "Coforge Ltd"),
    ("HAPPSTMNDS",  "Happiest Minds Tech"),
    ("TANLA",       "Tanla Platforms"),
    ("ROUTE",       "Route Mobile"),
    ("INDIAMART",   "IndiaMART InterMESH"),
    ("NAUKRI",      "Info Edge (Naukri)"),
    ("AFFLE",       "Affle India"),
    ("CLEAN",       "Clean Science & Tech"),
    ("FINEORG",     "Fine Organic Industries"),
    ("TATACHEM",    "Tata Chemicals"),
    ("ATUL",        "Atul Ltd"),
    ("NAVINFLUOR",  "Navin Fluorine"),
    ("SRF",         "SRF Ltd"),
    ("DEEPAKNTR",   "Deepak Nitrite"),
    ("AAVAS",       "Aavas Financiers"),
    ("HOMEFIRST",   "Home First Finance"),
    ("CANFINHOME",  "Can Fin Homes"),
    ("LICHSGFIN",   "LIC Housing Finance"),
    ("PNBHOUSING",  "PNB Housing Finance"),
    ("LICI",        "Life Insurance Corp (LIC)"),
    ("GICRE",       "General Insurance Corp"),
    ("NIACL",       "New India Assurance"),
    ("STARHEALTH",  "Star Health Insurance"),
    ("ICICIGI",     "ICICI Lombard General"),
    ("360ONE",      "360 ONE WAM"),
    ("ANGELONE",    "Angel One"),
    ("MOTILALOFS",  "Motilal Oswal Financial"),
    ("BSE",         "BSE Ltd"),
    ("CDSL",        "CDSL"),
    ("MCX",         "Multi Commodity Exchange"),
    ("CAMS",        "Computer Age Mgmt (CAMS)"),
    ("KFINTECH",    "KFin Technologies"),
]

# ── Index Symbols ──
INDICES = [
    {"sym": "NIFTY 50",   "yf": "^NSEI",   "name": "Nifty 50"},
    {"sym": "SENSEX",     "yf": "^BSESN",  "name": "BSE Sensex"},
    {"sym": "NIFTY BANK", "yf": "^NSEBANK","name": "Nifty Bank"},
    {"sym": "NIFTY IT",   "yf": "^CNXIT",  "name": "Nifty IT"},
    {"sym": "BTC",        "yf": "BTC-USD", "name": "Bitcoin"},
    {"sym": "GOLD",       "yf": "GC=F",    "name": "Gold Futures"},
]

STOCK_LOOKUP = {sym: name for sym, name in NIFTY500}

# Top 50 pre-fetched on startup
TOP50_SYMS = [
    "RELIANCE","TCS","HDFCBANK","BHARTIARTL","ICICIBANK",
    "INFOSYS","SBIN","HINDUNILVR","ITC","LT",
    "BAJFINANCE","HCLTECH","MARUTI","SUNPHARMA","ADANIENT",
    "KOTAKBANK","AXISBANK","WIPRO","ULTRACEMCO","TITAN",
    "ASIANPAINT","NESTLEIND","POWERGRID","NTPC","TATAMOTORS",
    "TECHM","INDUSINDBK","BAJAJFINSV","JSWSTEEL","TATASTEEL",
    "COALINDIA","ONGC","ADANIPORTS","GRASIM","BRITANNIA",
    "CIPLA","DRREDDY","HEROMOTOCO","HINDALCO","DIVISLAB",
    "EICHERMOT","BPCL","TATACONSUM","APOLLOHOSP","BAJAJ-AUTO",
    "VEDL","SBILIFE","HDFCLIFE","ZOMATO","IRCTC",
]

_cache = {
    "top50": [],
    "indices": [],
    "all_symbols": [{"sym": s, "name": n} for s, n in NIFTY500],
    "last_updated": None
}
_cache_lock = threading.Lock()
CACHE_TTL = 90


def fetch_quote(symbol_yf):
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
            return {"price": f"{price:,.2f}", "chg": chg_str, "up": up, "chg_raw": chg_pct}
    except Exception as e:
        print(f"  x {symbol_yf}: {e}")
    return {"price": "N/A", "chg": "—", "up": True, "chg_raw": 0}


def refresh_cache():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Refreshing Top 50 + Indices...")
    top50_data = []
    for sym in TOP50_SYMS:
        yf_sym = sym.replace(" ","") + ".NS"
        q = fetch_quote(yf_sym)
        top50_data.append({
            "sym": sym, "name": STOCK_LOOKUP.get(sym, sym),
            "price": q["price"], "chg": q["chg"], "up": q["up"], "chg_raw": q["chg_raw"]
        })
        print(f"  {sym:15} Rs.{q['price']:>12}  {q['chg']}")

    indices_data = []
    for idx in INDICES:
        q = fetch_quote(idx["yf"])
        indices_data.append({"sym": idx["sym"], "name": idx["name"],
                              "price": q["price"], "chg": q["chg"], "up": q["up"]})
        print(f"  {idx['sym']:15}  {q['price']:>12}  {q['chg']}")

    with _cache_lock:
        _cache["top50"] = top50_data
        _cache["indices"] = indices_data
        _cache["last_updated"] = datetime.now().isoformat()
    print(f"  Done. {len(top50_data)} stocks cached.\n")


def background_refresher():
    while True:
        try:
            refresh_cache()
        except Exception as e:
            print(f"Background error: {e}")
        time.sleep(CACHE_TTL)


@app.route("/api/all")
def api_all():
    with _cache_lock:
        return jsonify({"stocks": _cache["top50"], "indices": _cache["indices"],
                        "last_updated": _cache["last_updated"], "source": "Yahoo Finance (NSE)"})

@app.route("/api/stocks")
def api_stocks():
    with _cache_lock:
        return jsonify({"data": _cache["top50"], "last_updated": _cache["last_updated"]})

@app.route("/api/indices")
def api_indices():
    with _cache_lock:
        return jsonify({"data": _cache["indices"], "last_updated": _cache["last_updated"]})

@app.route("/api/symbols")
def api_symbols():
    with _cache_lock:
        return jsonify({"symbols": _cache["all_symbols"], "count": len(_cache["all_symbols"])})

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    sym_clean = symbol.upper().replace(" ","")
    with _cache_lock:
        for s in _cache["top50"]:
            if s["sym"].upper() == sym_clean:
                return jsonify({"symbol": sym_clean, "name": s["name"],
                                "price": s["price"], "chg": s["chg"], "up": s["up"], "source": "cache"})
    print(f"  Live fetch: {sym_clean}")
    q = fetch_quote(sym_clean + ".NS")
    return jsonify({"symbol": sym_clean, "name": STOCK_LOOKUP.get(sym_clean, sym_clean),
                    "price": q["price"], "chg": q["chg"], "up": q["up"], "source": "live"})

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify({"results": [], "query": query})
    results = [{"sym": s, "name": n} for s, n in NIFTY500
               if query in s.lower() or query in n.lower()][:20]
    return jsonify({"results": results, "query": query, "count": len(results)})

@app.route("/api/status")
def api_status():
    with _cache_lock:
        return jsonify({"status": "running", "last_updated": _cache["last_updated"],
                        "cached_stocks": len(_cache["top50"]),
                        "total_symbols": len(_cache["all_symbols"])})

@app.route("/")
def index():
    with _cache_lock:
        lu = _cache["last_updated"] or "not yet"
        count = len(_cache["top50"])
    return f"""<html><body style="font-family:monospace;background:#080b10;color:#c8d8e8;padding:30px">
    <h2 style="color:#00e5ff">MarketPit API Server</h2>
    <p>Last updated: <strong style="color:#00ff88">{lu}</strong> | Stocks cached: <strong style="color:#00ff88">{count}</strong></p>
    <hr style="border-color:#1e2d3d;margin:16px 0">
    <ul>
      <li><a href="/api/all" style="color:#00e5ff">/api/all</a> — Top 50 + indices</li>
      <li><a href="/api/symbols" style="color:#00e5ff">/api/symbols</a> — All {len(NIFTY500)} symbol names</li>
      <li><a href="/api/quote/RELIANCE" style="color:#00e5ff">/api/quote/RELIANCE</a> — Any single stock</li>
      <li><a href="/api/search?q=tata" style="color:#00e5ff">/api/search?q=tata</a> — Search stocks</li>
      <li><a href="/api/status" style="color:#00e5ff">/api/status</a> — Server status</li>
    </ul>
    </body></html>"""

if __name__ == "__main__":
    print("=" * 55)
    print("  MarketPit Backend — Nifty 500 Edition")
    print(f"  Total symbols loaded: {len(NIFTY500)}")
    print("=" * 55)
    refresh_cache()
    t = threading.Thread(target=background_refresher, daemon=True)
    t.start()
    print("Server running at http://localhost:5000")
    print("Open marketpit.html in your browser\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
