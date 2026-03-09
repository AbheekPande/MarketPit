"""
MarketPit — Python Backend Server (Railway Edition)
Fetches real-time Indian stock data from Yahoo Finance (yfinance)
"""

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import threading
import time
import os
import urllib.request

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

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
        hist   = ticker.history(period="1y")
        if hist.empty:
            return jsonify({"error": "No data"}), 404

        close  = hist["Close"]
        high   = hist["High"]
        low    = hist["Low"]
        volume = hist["Volume"]
        price  = round(float(close.iloc[-1]), 2)

        def r(v, d=2):
            try: return round(float(v), d)
            except: return None

        # ── MOVING AVERAGES ──
        ma10  = r(close.tail(10).mean())  if len(close) >= 10  else None
        ma20  = r(close.tail(20).mean())  if len(close) >= 20  else None
        ma50  = r(close.tail(50).mean())  if len(close) >= 50  else None
        ma100 = r(close.tail(100).mean()) if len(close) >= 100 else None
        ma200 = r(close.tail(200).mean()) if len(close) >= 200 else None

        # EMA
        ema9   = r(close.ewm(span=9,   adjust=False).mean().iloc[-1])
        ema21  = r(close.ewm(span=21,  adjust=False).mean().iloc[-1])
        ema50  = r(close.ewm(span=50,  adjust=False).mean().iloc[-1])
        ema200 = r(close.ewm(span=200, adjust=False).mean().iloc[-1]) if len(close) >= 200 else None

        # ── RSI (14) ──
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss
        rsi   = r(100 - (100 / (1 + rs.iloc[-1])), 1)

        # RSI (7) — faster
        gain7 = delta.clip(lower=0).rolling(7).mean()
        loss7 = (-delta.clip(upper=0)).rolling(7).mean()
        rs7   = gain7 / loss7
        rsi7  = r(100 - (100 / (1 + rs7.iloc[-1])), 1)

        # ── MACD ──
        ema12       = close.ewm(span=12, adjust=False).mean()
        ema26       = close.ewm(span=26, adjust=False).mean()
        macd_line   = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist   = macd_line - signal_line
        macd_val    = r(macd_line.iloc[-1])
        signal_val  = r(signal_line.iloc[-1])
        macd_hist_val = r(macd_hist.iloc[-1])
        macd_bullish  = macd_val > signal_val
        # MACD histogram trend (increasing = strengthening)
        macd_increasing = macd_hist.iloc[-1] > macd_hist.iloc[-2]

        # ── BOLLINGER BANDS (20) ──
        sma20   = close.rolling(20).mean()
        std20   = close.rolling(20).std()
        bb_upper = r((sma20 + 2*std20).iloc[-1])
        bb_lower = r((sma20 - 2*std20).iloc[-1])
        bb_mid   = r(sma20.iloc[-1])
        bb_width = r(((bb_upper - bb_lower) / bb_mid) * 100, 1) if bb_mid else None
        bb_pct   = r(((price - bb_lower) / (bb_upper - bb_lower)) * 100, 1) if bb_upper and bb_lower else None

        # ── STOCHASTIC OSCILLATOR (14,3) ──
        low14  = low.rolling(14).min()
        high14 = high.rolling(14).max()
        stoch_k = r(((close - low14) / (high14 - low14) * 100).iloc[-1], 1)
        stoch_d = r(((close - low14) / (high14 - low14) * 100).rolling(3).mean().iloc[-1], 1)
        stoch_bullish = stoch_k and stoch_d and stoch_k > stoch_d

        # ── ATR (Average True Range, 14) ──
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low  - close.shift()).abs()
        tr  = tr1.combine(tr2, max).combine(tr3, max)
        atr = r(tr.rolling(14).mean().iloc[-1])
        atr_pct = r((atr / price) * 100, 2) if atr and price else None

        # ── ADX (Average Directional Index, 14) ──
        try:
            plus_dm  = high.diff().clip(lower=0)
            minus_dm = (-low.diff()).clip(lower=0)
            atr14    = tr.rolling(14).mean()
            plus_di  = 100 * (plus_dm.rolling(14).mean()  / atr14)
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
            dx       = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di))
            adx      = r(dx.rolling(14).mean().iloc[-1], 1)
            plus_di_val  = r(plus_di.iloc[-1], 1)
            minus_di_val = r(minus_di.iloc[-1], 1)
        except:
            adx = plus_di_val = minus_di_val = None

        # ── CCI (Commodity Channel Index, 20) ──
        try:
            tp  = (high + low + close) / 3
            cci = r(((tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std())).iloc[-1], 1)
        except:
            cci = None

        # ── WILLIAMS %R (14) ──
        try:
            wr = r((-(high.rolling(14).max() - close) / (high.rolling(14).max() - low.rolling(14).min()) * 100).iloc[-1], 1)
        except:
            wr = None

        # ── VWAP (current session approx using 20 days) ──
        try:
            tp_vwap = (high + low + close) / 3
            vwap = r((tp_vwap * volume).tail(20).sum() / volume.tail(20).sum())
        except:
            vwap = None

        # ── VOLUME ANALYSIS ──
        vol_avg20   = r(volume.tail(20).mean())
        vol_current = r(float(volume.iloc[-1]))
        vol_ratio   = r(vol_current / vol_avg20, 2) if vol_avg20 and vol_avg20 > 0 else None
        vol_spike   = vol_ratio and vol_ratio > 1.5

        # ── SUPPORT & RESISTANCE ──
        support_20    = r(low.tail(20).min())
        resistance_20 = r(high.tail(20).max())
        support_50    = r(low.tail(50).min())
        resistance_50 = r(high.tail(50).max())

        # Pivot Points (Classic — based on last session)
        prev_high  = r(float(high.iloc[-2]))
        prev_low   = r(float(low.iloc[-2]))
        prev_close = r(float(close.iloc[-2]))
        if prev_high and prev_low and prev_close:
            pivot  = r((prev_high + prev_low + prev_close) / 3)
            r1     = r(2 * pivot - prev_low)
            r2     = r(pivot + (prev_high - prev_low))
            s1     = r(2 * pivot - prev_high)
            s2     = r(pivot - (prev_high - prev_low))
        else:
            pivot = r1 = r2 = s1 = s2 = None

        # ── PRICE ACTION ──
        change_1d  = r(((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100, 2)
        change_1w  = r(((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]) * 100, 2)  if len(close) >= 6   else None
        change_1m  = r(((close.iloc[-1] - close.iloc[-22]) / close.iloc[-22]) * 100, 2) if len(close) >= 22 else None
        change_3m  = r(((close.iloc[-1] - close.iloc[-66]) / close.iloc[-66]) * 100, 2) if len(close) >= 66 else None
        change_6m  = r(((close.iloc[-1] - close.iloc[-132]) / close.iloc[-132]) * 100, 2) if len(close) >= 132 else None
        high_52w   = r(float(high.tail(252).max()))
        low_52w    = r(float(low.tail(252).min()))
        pct_from_52h = r(((price - high_52w) / high_52w) * 100, 2) if high_52w else None
        pct_from_52l = r(((price - low_52w)  / low_52w)  * 100, 2) if low_52w  else None

        # ── TREND STRENGTH ──
        # Price position relative to MAs
        above_ma50  = price > ma50  if ma50  else None
        above_ma200 = price > ma200 if ma200 else None
        golden_cross = (ma50 and ma200 and ma50 > ma200)   # MA50 > MA200 = bullish
        death_cross  = (ma50 and ma200 and ma50 < ma200)

        # ── OVERALL SIGNAL (expanded to 8 indicators) ──
        signals = []
        if ma50:  signals.append("BUY"  if price > ma50  else "SELL")
        if ma200: signals.append("BUY"  if price > ma200 else "SELL")
        if rsi:
            if rsi < 30:   signals.append("BUY")
            elif rsi > 70: signals.append("SELL")
            else:          signals.append("HOLD")
        signals.append("BUY" if macd_bullish else "SELL")
        if stoch_k:
            if stoch_k < 20:   signals.append("BUY")
            elif stoch_k > 80: signals.append("SELL")
            else:              signals.append("HOLD")
        if cci:
            if cci < -100:  signals.append("BUY")
            elif cci > 100: signals.append("SELL")
            else:           signals.append("HOLD")
        if adx and adx > 25:
            signals.append("BUY" if (plus_di_val and minus_di_val and plus_di_val > minus_di_val) else "SELL")
        if vwap:
            signals.append("BUY" if price > vwap else "SELL")

        buy_count  = signals.count("BUY")
        sell_count = signals.count("SELL")
        total      = len(signals)
        if   buy_count >= round(total * 0.75):  overall = "STRONG BUY"
        elif buy_count >= round(total * 0.5):   overall = "BUY"
        elif sell_count >= round(total * 0.75): overall = "STRONG SELL"
        elif sell_count >= round(total * 0.5):  overall = "SELL"
        else:                                    overall = "HOLD"

        sparkline = [r(x) for x in close.tail(30).tolist()]

        return jsonify({
            "symbol":   symbol.upper(),
            "price":    price,
            # Moving Averages
            "ma10": ma10, "ma20": ma20, "ma50": ma50, "ma100": ma100, "ma200": ma200,
            "ema9": ema9, "ema21": ema21, "ema50": ema50, "ema200": ema200,
            # RSI
            "rsi": rsi, "rsi7": rsi7,
            # MACD
            "macd": macd_val, "macd_signal": signal_val,
            "macd_hist": macd_hist_val, "macd_bullish": macd_bullish,
            "macd_increasing": macd_increasing,
            # Bollinger Bands
            "bb_upper": bb_upper, "bb_lower": bb_lower, "bb_mid": bb_mid,
            "bb_width": bb_width, "bb_pct": bb_pct,
            # Stochastic
            "stoch_k": stoch_k, "stoch_d": stoch_d, "stoch_bullish": stoch_bullish,
            # ATR
            "atr": atr, "atr_pct": atr_pct,
            # ADX
            "adx": adx, "plus_di": plus_di_val, "minus_di": minus_di_val,
            # CCI & Williams %R
            "cci": cci, "williams_r": wr,
            # VWAP
            "vwap": vwap,
            # Volume
            "vol_avg20": vol_avg20, "vol_current": vol_current,
            "vol_ratio": vol_ratio, "vol_spike": vol_spike,
            # Support & Resistance
            "support": support_20, "resistance": resistance_20,
            "support_50": support_50, "resistance_50": resistance_50,
            # Pivot Points
            "pivot": pivot, "r1": r1, "r2": r2, "s1": s1, "s2": s2,
            # Price Performance
            "change_1d": change_1d, "change_1w": change_1w,
            "change_1m": change_1m, "change_3m": change_3m, "change_6m": change_6m,
            "high_52w": high_52w, "low_52w": low_52w,
            "pct_from_52h": pct_from_52h, "pct_from_52l": pct_from_52l,
            # Trend
            "above_ma50": above_ma50, "above_ma200": above_ma200,
            "golden_cross": golden_cross, "death_cross": death_cross,
            # Signal
            "overall": overall, "buy_signals": buy_count,
            "sell_signals": sell_count, "total_signals": total,
            "sparkline": sparkline
        })
    except Exception as e:
        print(f"Technical error {symbol}: {e}")
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


def keep_alive():
    """Ping self every 10 minutes to prevent Railway from sleeping"""
    time.sleep(60)  # wait for server to start
    port = int(os.environ.get("PORT", 5000))
    url = f"http://localhost:{port}/api/status"
    while True:
        try:
            urllib.request.urlopen(url, timeout=5)
            print(f"[{datetime.now().strftime('%H:%M')}] Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive failed: {e}")
        time.sleep(600)  # ping every 10 minutes

if __name__ == "__main__":
    print("=" * 55)
    print("  MarketPit Backend — Railway Edition")
    print(f"  Total symbols: {len(NIFTY500)}")
    print("=" * 55)
    refresh_cache()
    t = threading.Thread(target=background_refresher, daemon=True)
    t.start()
    k = threading.Thread(target=keep_alive, daemon=True)
    k.start()
    # Railway uses PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    print(f"Server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
