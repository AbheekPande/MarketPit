"""
MarketPit — Python Backend Server (Railway Edition)
Fetches real-time Indian stock data from Yahoo Finance (yfinance)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import threading
import time
import os

app = Flask(__name__)
CORS(app)  # Allow all origins so the HTML frontend can connect

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
    ("ALKEM",       "Alkem Laboratories"),
    ("LALPATHLAB",  "Dr Lal PathLabs"),
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
    ("VBL",         "Varun Beverages"),
    ("JUBLFOOD",    "Jubilant Foodworks"),
    ("PVRINOX",     "PVR INOX"),
    ("TATAELXSI",   "Tata Elxsi"),
    ("KPIT",        "KPIT Technologies"),
    ("LTTS",        "L&T Technology Services"),
    ("PERSISTENT",  "Persistent Systems"),
    ("MPHASIS",     "Mphasis Ltd"),
    ("COFORGE",     "Coforge Ltd"),
    ("HAPPSTMNDS",  "Happiest Minds Tech"),
    ("TANLA",       "Tanla Platforms"),
    ("INDIAMART",   "IndiaMART InterMESH"),
    ("NAUKRI",      "Info Edge (Naukri)"),
    ("AFFLE",       "Affle India"),
    ("CLEAN",       "Clean Science & Tech"),
    ("TATACHEM",    "Tata Chemicals"),
    ("ATUL",        "Atul Ltd"),
    ("NAVINFLUOR",  "Navin Fluorine"),
    ("SRF",         "SRF Ltd"),
    ("DEEPAKNTR",   "Deepak Nitrite"),
    ("LICHSGFIN",   "LIC Housing Finance"),
    ("LICI",        "Life Insurance Corp (LIC)"),
    ("GICRE",       "General Insurance Corp"),
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

INDICES = [
    {"sym": "NIFTY 50",   "yf": "^NSEI",   "name": "Nifty 50"},
    {"sym": "SENSEX",     "yf": "^BSESN",  "name": "BSE Sensex"},
    {"sym": "NIFTY BANK", "yf": "^NSEBANK","name": "Nifty Bank"},
    {"sym": "NIFTY IT",   "yf": "^CNXIT",  "name": "Nifty IT"},
    {"sym": "BTC",        "yf": "BTC-USD", "name": "Bitcoin"},
    {"sym": "GOLD",       "yf": "GC=F",    "name": "Gold Futures"},
]

STOCK_LOOKUP = {sym: name for sym, name in NIFTY500}

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
    "VEDL","SBILIFE","HDFCLIFE","IRCTC","LICI",
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
            return {
                "price": f"{price:,.2f}",
                "chg": chg_str,
                "up": up,
                "chg_raw": chg_pct,
                "high": f"{round(info.day_high,2):,.2f}" if info.day_high else None,
                "low": f"{round(info.day_low,2):,.2f}" if info.day_low else None,
                "volume": int(info.three_month_average_volume) if info.three_month_average_volume else None,
                "week52high": f"{round(info.year_high,2):,.2f}" if info.year_high else None,
                "week52low": f"{round(info.year_low,2):,.2f}" if info.year_low else None,
                "marketcap": int(info.market_cap) if info.market_cap else None,
            }
    except Exception as e:
        print(f"  x {symbol_yf}: {e}")
    return {"price": "N/A", "chg": "—", "up": True, "chg_raw": 0}


def refresh_cache():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Refreshing...")
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

# ── CRYPTO & COMMODITY LOOKUP ──
CRYPTO_LOOKUP = {
    "BTC": ("BTC-USD", "Bitcoin"),
    "BITCOIN": ("BTC-USD", "Bitcoin"),
    "ETH": ("ETH-USD", "Ethereum"),
    "ETHEREUM": ("ETH-USD", "Ethereum"),
    "BNB": ("BNB-USD", "Binance Coin"),
    "SOL": ("SOL-USD", "Solana"),
    "XRP": ("XRP-USD", "XRP"),
    "ADA": ("ADA-USD", "Cardano"),
    "DOGE": ("DOGE-USD", "Dogecoin"),
    "MATIC": ("MATIC-USD", "Polygon"),
    "DOT": ("DOT-USD", "Polkadot"),
    "AVAX": ("AVAX-USD", "Avalanche"),
    "LINK": ("LINK-USD", "Chainlink"),
    "LTC": ("LTC-USD", "Litecoin"),
    "UNI": ("UNI-USD", "Uniswap"),
    "ATOM": ("ATOM-USD", "Cosmos"),
    "SHIB": ("SHIB-USD", "Shiba Inu"),
    "PEPE": ("PEPE-USD", "Pepe"),
    "TON": ("TON11419-USD", "Toncoin"),
    "INJ": ("INJ-USD", "Injective"),
}

COMMODITY_LOOKUP = {
    "GOLD": ("GC=F", "Gold Futures"),
    "SILVER": ("SI=F", "Silver Futures"),
    "CRUDE": ("CL=F", "Crude Oil WTI"),
    "OIL": ("CL=F", "Crude Oil WTI"),
    "CRUDEOIL": ("CL=F", "Crude Oil WTI"),
    "BRENT": ("BZ=F", "Brent Crude Oil"),
    "NATURALGAS": ("NG=F", "Natural Gas"),
    "GAS": ("NG=F", "Natural Gas"),
    "COPPER": ("HG=F", "Copper Futures"),
    "PLATINUM": ("PL=F", "Platinum Futures"),
    "WHEAT": ("ZW=F", "Wheat Futures"),
    "CORN": ("ZC=F", "Corn Futures"),
    "ALUMINIUM": ("ALI=F", "Aluminium Futures"),
    "NICKEL": ("NI=F", "Nickel Futures"),
}

def resolve_symbol(raw):
    """Returns (yf_symbol, display_name, currency_prefix, asset_type)"""
    key = raw.upper().replace(" ","").replace("-","")
    if key in CRYPTO_LOOKUP:
        yf_sym, name = CRYPTO_LOOKUP[key]
        return yf_sym, name, "$", "crypto"
    if key in COMMODITY_LOOKUP:
        yf_sym, name = COMMODITY_LOOKUP[key]
        return yf_sym, name, "$", "commodity"
    # Indian stock default
    return key + ".NS", STOCK_LOOKUP.get(key, key), "₹", "stock"


@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    yf_sym, name, prefix, asset_type = resolve_symbol(symbol)
    q = fetch_quote(yf_sym)
    return jsonify({
        "symbol": symbol.upper(),
        "name": name,
        "price": q.get("price"),
        "chg": q.get("chg"),
        "up": q.get("up"),
        "high": q.get("high"),
        "low": q.get("low"),
        "volume": q.get("volume"),
        "week52high": q.get("week52high"),
        "week52low": q.get("week52low"),
        "marketcap": q.get("marketcap"),
        "currency": prefix,
        "asset_type": asset_type,
        "source": "live"
    })

@app.route("/api/technical/<symbol>")
def api_technical(symbol):
    yf_sym, display_name, prefix, asset_type = resolve_symbol(symbol)
    try:
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period="6mo")
        if hist.empty:
            return jsonify({"error": "No data"}), 404

        close = hist["Close"]
        price = round(float(close.iloc[-1]), 2)

        # Moving Averages
        ma50  = round(float(close.tail(50).mean()), 2)  if len(close) >= 50  else None
        ma200 = round(float(close.tail(200).mean()), 2) if len(close) >= 200 else None

        # RSI (14 period)
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss
        rsi   = round(float(100 - (100 / (1 + rs.iloc[-1]))), 1)

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line   = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_val    = round(float(macd_line.iloc[-1]), 2)
        signal_val  = round(float(signal_line.iloc[-1]), 2)
        macd_bullish = macd_val > signal_val

        # Bollinger Bands (20 period)
        ma20  = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bb_upper = round(float((ma20 + 2*std20).iloc[-1]), 2)
        bb_lower = round(float((ma20 - 2*std20).iloc[-1]), 2)
        bb_mid   = round(float(ma20.iloc[-1]), 2)

        # Support & Resistance (recent 20-day low/high)
        support    = round(float(hist["Low"].tail(20).min()), 2)
        resistance = round(float(hist["High"].tail(20).max()), 2)

        # Overall signal
        signals = []
        if ma50 and price > ma50:   signals.append("BUY")
        else:                        signals.append("SELL")
        if ma200 and price > ma200: signals.append("BUY")
        else:                        signals.append("SELL")
        if rsi < 30:                 signals.append("BUY")
        elif rsi > 70:               signals.append("SELL")
        else:                        signals.append("HOLD")
        if macd_bullish:             signals.append("BUY")
        else:                        signals.append("SELL")

        buy_count  = signals.count("BUY")
        sell_count = signals.count("SELL")
        if buy_count >= 3:   overall = "STRONG BUY"
        elif buy_count == 2: overall = "BUY"
        elif sell_count >= 3:overall = "STRONG SELL"
        elif sell_count == 2:overall = "SELL"
        else:                overall = "HOLD"

        # Sparkline (last 30 days closing prices)
        sparkline = [round(float(x), 2) for x in close.tail(30).tolist()]

        return jsonify({
            "symbol": sym_clean,
            "price": price,
            "ma50": ma50,
            "ma200": ma200,
            "rsi": rsi,
            "macd": macd_val,
            "macd_signal": signal_val,
            "macd_bullish": macd_bullish,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "bb_mid": bb_mid,
            "support": support,
            "resistance": resistance,
            "overall": overall,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "sparkline": sparkline
        })
    except Exception as e:
        print(f"Technical error {sym_clean}: {e}")
        return jsonify({"error": str(e)}), 500

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
    <h2 style="color:#00e5ff">MarketPit API Server Running!</h2>
    <p>Last updated: <strong style="color:#00ff88">{lu}</strong> | Stocks cached: <strong style="color:#00ff88">{count}</strong></p>
    <ul>
      <li><a href="/api/all" style="color:#00e5ff">/api/all</a> — Top 50 + indices</li>
      <li><a href="/api/symbols" style="color:#00e5ff">/api/symbols</a> — All symbols</li>
      <li><a href="/api/quote/RELIANCE" style="color:#00e5ff">/api/quote/RELIANCE</a> — Single stock</li>
      <li><a href="/api/search?q=tata" style="color:#00e5ff">/api/search?q=tata</a> — Search</li>
    </ul>
    </body></html>"""


if __name__ == "__main__":
    print("=" * 55)
    print("  MarketPit Backend — Railway Edition")
    print(f"  Total symbols: {len(NIFTY500)}")
    print("=" * 55)
    refresh_cache()
    t = threading.Thread(target=background_refresher, daemon=True)
    t.start()
    # Railway uses PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    print(f"Server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
