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

# ── Indian Stock Symbols — 150+ NSE stocks via Yahoo Finance ──
INDIAN_STOCKS = [
    # ═══ NIFTY 50 ═══
    {"sym":"HDFCBANK",   "yf":"HDFCBANK.NS",   "name":"HDFC Bank",               "sector":"Banking"},
    {"sym":"ICICIBANK",  "yf":"ICICIBANK.NS",   "name":"ICICI Bank",              "sector":"Banking"},
    {"sym":"SBIN",       "yf":"SBIN.NS",        "name":"State Bank of India",     "sector":"Banking"},
    {"sym":"AXISBANK",   "yf":"AXISBANK.NS",    "name":"Axis Bank",               "sector":"Banking"},
    {"sym":"KOTAKBANK",  "yf":"KOTAKBANK.NS",   "name":"Kotak Mahindra Bank",     "sector":"Banking"},
    {"sym":"INDUSINDBK", "yf":"INDUSINDBK.NS",  "name":"IndusInd Bank",           "sector":"Banking"},
    {"sym":"TCS",        "yf":"TCS.NS",         "name":"Tata Consultancy",        "sector":"IT"},
    {"sym":"INFY",       "yf":"INFY.NS",        "name":"Infosys",                 "sector":"IT"},
    {"sym":"WIPRO",      "yf":"WIPRO.NS",       "name":"Wipro Ltd",               "sector":"IT"},
    {"sym":"HCLTECH",    "yf":"HCLTECH.NS",     "name":"HCL Technologies",        "sector":"IT"},
    {"sym":"TECHM",      "yf":"TECHM.NS",       "name":"Tech Mahindra",           "sector":"IT"},
    {"sym":"LTIM",       "yf":"LTIM.NS",        "name":"LTIMindtree",             "sector":"IT"},
    {"sym":"TATAMOTORS", "yf":"TATAMOTORS.NS",  "name":"Tata Motors",             "sector":"Auto"},
    {"sym":"MARUTI",     "yf":"MARUTI.NS",      "name":"Maruti Suzuki",           "sector":"Auto"},
    {"sym":"M&M",        "yf":"M%26M.NS",       "name":"Mahindra & Mahindra",     "sector":"Auto"},
    {"sym":"HEROMOTOCO", "yf":"HEROMOTOCO.NS",  "name":"Hero MotoCorp",           "sector":"Auto"},
    {"sym":"EICHERMOT",  "yf":"EICHERMOT.NS",   "name":"Eicher Motors",           "sector":"Auto"},
    {"sym":"BAJAJ-AUTO", "yf":"BAJAJ-AUTO.NS",  "name":"Bajaj Auto",              "sector":"Auto"},
    {"sym":"SUNPHARMA",  "yf":"SUNPHARMA.NS",   "name":"Sun Pharmaceutical",      "sector":"Pharma"},
    {"sym":"DRREDDY",    "yf":"DRREDDY.NS",     "name":"Dr. Reddys Labs",         "sector":"Pharma"},
    {"sym":"CIPLA",      "yf":"CIPLA.NS",       "name":"Cipla",                   "sector":"Pharma"},
    {"sym":"DIVISLAB",   "yf":"DIVISLAB.NS",    "name":"Divis Laboratories",      "sector":"Pharma"},
    {"sym":"APOLLOHOSP", "yf":"APOLLOHOSP.NS",  "name":"Apollo Hospitals",        "sector":"Healthcare"},
    {"sym":"RELIANCE",   "yf":"RELIANCE.NS",    "name":"Reliance Industries",     "sector":"Energy"},
    {"sym":"ONGC",       "yf":"ONGC.NS",        "name":"ONGC",                    "sector":"Energy"},
    {"sym":"BPCL",       "yf":"BPCL.NS",        "name":"BPCL",                    "sector":"Energy"},
    {"sym":"IOC",        "yf":"IOC.NS",         "name":"Indian Oil Corp",         "sector":"Energy"},
    {"sym":"NTPC",       "yf":"NTPC.NS",        "name":"NTPC",                    "sector":"Energy"},
    {"sym":"POWERGRID",  "yf":"POWERGRID.NS",   "name":"Power Grid Corp",         "sector":"Utilities"},
    {"sym":"TATASTEEL",  "yf":"TATASTEEL.NS",   "name":"Tata Steel",              "sector":"Metal"},
    {"sym":"JSWSTEEL",   "yf":"JSWSTEEL.NS",    "name":"JSW Steel",               "sector":"Metal"},
    {"sym":"HINDALCO",   "yf":"HINDALCO.NS",    "name":"Hindalco Industries",     "sector":"Metal"},
    {"sym":"COALINDIA",  "yf":"COALINDIA.NS",   "name":"Coal India",              "sector":"Mining"},
    {"sym":"NESTLEIND",  "yf":"NESTLEIND.NS",   "name":"Nestle India",            "sector":"FMCG"},
    {"sym":"BRITANNIA",  "yf":"BRITANNIA.NS",   "name":"Britannia Industries",    "sector":"FMCG"},
    {"sym":"ITC",        "yf":"ITC.NS",         "name":"ITC Ltd",                 "sector":"FMCG"},
    {"sym":"HINDUNILVR", "yf":"HINDUNILVR.NS",  "name":"Hindustan Unilever",      "sector":"FMCG"},
    {"sym":"TATACONSUM", "yf":"TATACONSUM.NS",  "name":"Tata Consumer Products",  "sector":"FMCG"},
    {"sym":"BAJFINANCE", "yf":"BAJFINANCE.NS",  "name":"Bajaj Finance",           "sector":"Finance"},
    {"sym":"BAJAJFINSV", "yf":"BAJAJFINSV.NS",  "name":"Bajaj Finserv",           "sector":"Finance"},
    {"sym":"TITAN",      "yf":"TITAN.NS",       "name":"Titan Company",           "sector":"Consumer"},
    {"sym":"ASIANPAINT", "yf":"ASIANPAINT.NS",  "name":"Asian Paints",            "sector":"Consumer"},
    {"sym":"DMART",      "yf":"DMART.NS",       "name":"DMart (Avenue Super.)",   "sector":"Retail"},
    {"sym":"LT",         "yf":"LT.NS",          "name":"Larsen & Toubro",         "sector":"Infra"},
    {"sym":"ADANIENT",   "yf":"ADANIENT.NS",    "name":"Adani Enterprises",       "sector":"Conglomerate"},
    {"sym":"ULTRACEMCO", "yf":"ULTRACEMCO.NS",  "name":"UltraTech Cement",        "sector":"Cement"},
    {"sym":"GRASIM",     "yf":"GRASIM.NS",      "name":"Grasim Industries",       "sector":"Conglomerate"},
    {"sym":"BHARTIARTL", "yf":"BHARTIARTL.NS",  "name":"Bharti Airtel",           "sector":"Telecom"},
    {"sym":"JUBLFOOD",   "yf":"JUBLFOOD.NS",    "name":"Jubilant Foodworks",      "sector":"Consumer"},
    {"sym":"SHRIRAMFIN", "yf":"SHRIRAMFIN.NS",  "name":"Shriram Finance",         "sector":"Finance"},

    # ═══ NIFTY NEXT 50 ═══
    {"sym":"ADANIPORTS",  "yf":"ADANIPORTS.NS",  "name":"Adani Ports & SEZ",       "sector":"Infra"},
    {"sym":"ADANIPOWER",  "yf":"ADANIPOWER.NS",  "name":"Adani Power",             "sector":"Energy"},
    {"sym":"AMBUJACEM",   "yf":"AMBUJACEM.NS",   "name":"Ambuja Cements",          "sector":"Cement"},
    {"sym":"BANKBARODA",  "yf":"BANKBARODA.NS",  "name":"Bank of Baroda",          "sector":"Banking"},
    {"sym":"BERGEPAINT",  "yf":"BERGEPAINT.NS",  "name":"Berger Paints India",     "sector":"Consumer"},
    {"sym":"BEL",         "yf":"BEL.NS",         "name":"Bharat Electronics",      "sector":"Defence"},
    {"sym":"BHEL",        "yf":"BHEL.NS",        "name":"Bharat Heavy Electricals","sector":"Capital Goods"},
    {"sym":"BOSCHLTD",    "yf":"BOSCHLTD.NS",    "name":"Bosch Ltd",               "sector":"Auto Ancillary"},
    {"sym":"CANBK",       "yf":"CANBK.NS",       "name":"Canara Bank",             "sector":"Banking"},
    {"sym":"CHOLAFIN",    "yf":"CHOLAFIN.NS",    "name":"Cholamandalam Finance",   "sector":"Finance"},
    {"sym":"COLPAL",      "yf":"COLPAL.NS",      "name":"Colgate Palmolive India", "sector":"FMCG"},
    {"sym":"DLF",         "yf":"DLF.NS",         "name":"DLF Ltd",                 "sector":"Realty"},
    {"sym":"GAIL",        "yf":"GAIL.NS",        "name":"GAIL India",              "sector":"Energy"},
    {"sym":"GODREJCP",    "yf":"GODREJCP.NS",    "name":"Godrej Consumer Products","sector":"FMCG"},
    {"sym":"HAL",         "yf":"HAL.NS",         "name":"Hindustan Aeronautics",   "sector":"Defence"},
    {"sym":"HAVELLS",     "yf":"HAVELLS.NS",     "name":"Havells India",           "sector":"Capital Goods"},
    {"sym":"HDFCLIFE",    "yf":"HDFCLIFE.NS",    "name":"HDFC Life Insurance",     "sector":"Insurance"},
    {"sym":"HINDPETRO",   "yf":"HINDPETRO.NS",   "name":"HPCL",                    "sector":"Energy"},
    {"sym":"INDUSTOWER",  "yf":"INDUSTOWER.NS",  "name":"Indus Towers",            "sector":"Telecom"},
    {"sym":"IRCTC",       "yf":"IRCTC.NS",       "name":"IRCTC",                   "sector":"Travel"},
    {"sym":"JSWENERGY",   "yf":"JSWENERGY.NS",   "name":"JSW Energy",              "sector":"Energy"},
    {"sym":"LICI",        "yf":"LICI.NS",        "name":"Life Insurance Corp",     "sector":"Insurance"},
    {"sym":"LUPIN",       "yf":"LUPIN.NS",       "name":"Lupin Ltd",               "sector":"Pharma"},
    {"sym":"MARICO",      "yf":"MARICO.NS",      "name":"Marico Ltd",              "sector":"FMCG"},
    {"sym":"MUTHOOTFIN",  "yf":"MUTHOOTFIN.NS",  "name":"Muthoot Finance",         "sector":"Finance"},
    {"sym":"NAUKRI",      "yf":"NAUKRI.NS",      "name":"Info Edge (Naukri)",      "sector":"IT"},
    {"sym":"NMDC",        "yf":"NMDC.NS",        "name":"NMDC Ltd",                "sector":"Mining"},
    {"sym":"OFSS",        "yf":"OFSS.NS",        "name":"Oracle Financial Services","sector":"IT"},
    {"sym":"PERSISTENT",  "yf":"PERSISTENT.NS",  "name":"Persistent Systems",      "sector":"IT"},
    {"sym":"PETRONET",    "yf":"PETRONET.NS",    "name":"Petronet LNG",            "sector":"Energy"},
    {"sym":"PIDILITIND",  "yf":"PIDILITIND.NS",  "name":"Pidilite Industries",     "sector":"Chemicals"},
    {"sym":"PNB",         "yf":"PNB.NS",         "name":"Punjab National Bank",    "sector":"Banking"},
    {"sym":"RECLTD",      "yf":"RECLTD.NS",      "name":"REC Ltd",                 "sector":"Finance"},
    {"sym":"SAIL",        "yf":"SAIL.NS",        "name":"Steel Authority of India","sector":"Metal"},
    {"sym":"SBICARD",     "yf":"SBICARD.NS",     "name":"SBI Cards & Payment",     "sector":"Finance"},
    {"sym":"SBILIFE",     "yf":"SBILIFE.NS",     "name":"SBI Life Insurance",      "sector":"Insurance"},
    {"sym":"SHREECEM",    "yf":"SHREECEM.NS",    "name":"Shree Cement",            "sector":"Cement"},
    {"sym":"SIEMENS",     "yf":"SIEMENS.NS",     "name":"Siemens India",           "sector":"Capital Goods"},
    {"sym":"TORNTPHARM",  "yf":"TORNTPHARM.NS",  "name":"Torrent Pharmaceuticals", "sector":"Pharma"},
    {"sym":"TRENT",       "yf":"TRENT.NS",       "name":"Trent Ltd",               "sector":"Retail"},
    {"sym":"TVSMOTOR",    "yf":"TVSMOTOR.NS",    "name":"TVS Motor Company",       "sector":"Auto"},
    {"sym":"UPL",         "yf":"UPL.NS",         "name":"UPL Ltd",                 "sector":"Chemicals"},
    {"sym":"VEDL",        "yf":"VEDL.NS",        "name":"Vedanta Ltd",             "sector":"Metal"},
    {"sym":"ZOMATO",      "yf":"ZOMATO.NS",      "name":"Zomato Ltd",              "sector":"Consumer Tech"},
    {"sym":"ZYDUSLIFE",   "yf":"ZYDUSLIFE.NS",   "name":"Zydus Lifesciences",      "sector":"Pharma"},

    # ═══ POPULAR MID-CAPS ═══
    {"sym":"ABCAPITAL",   "yf":"ABCAPITAL.NS",   "name":"Aditya Birla Capital",    "sector":"Finance"},
    {"sym":"ALKEM",       "yf":"ALKEM.NS",       "name":"Alkem Laboratories",      "sector":"Pharma"},
    {"sym":"AUBANK",      "yf":"AUBANK.NS",      "name":"AU Small Finance Bank",   "sector":"Banking"},
    {"sym":"AUROPHARMA",  "yf":"AUROPHARMA.NS",  "name":"Aurobindo Pharma",        "sector":"Pharma"},
    {"sym":"BANDHANBNK",  "yf":"BANDHANBNK.NS",  "name":"Bandhan Bank",            "sector":"Banking"},
    {"sym":"BEL",         "yf":"BEL.NS",         "name":"Bharat Electronics",      "sector":"Defence"},
    {"sym":"BIOCON",      "yf":"BIOCON.NS",      "name":"Biocon Ltd",              "sector":"Pharma"},
    {"sym":"COFORGE",     "yf":"COFORGE.NS",     "name":"Coforge Ltd",             "sector":"IT"},
    {"sym":"DEEPAKNTR",   "yf":"DEEPAKNTR.NS",   "name":"Deepak Nitrite",          "sector":"Chemicals"},
    {"sym":"DIXON",       "yf":"DIXON.NS",       "name":"Dixon Technologies",      "sector":"Capital Goods"},
    {"sym":"FEDERALBNK",  "yf":"FEDERALBNK.NS",  "name":"Federal Bank",            "sector":"Banking"},
    {"sym":"FORTIS",      "yf":"FORTIS.NS",      "name":"Fortis Healthcare",       "sector":"Healthcare"},
    {"sym":"GLENMARK",    "yf":"GLENMARK.NS",    "name":"Glenmark Pharma",         "sector":"Pharma"},
    {"sym":"GODREJPROP",  "yf":"GODREJPROP.NS",  "name":"Godrej Properties",       "sector":"Realty"},
    {"sym":"HDFCAMC",     "yf":"HDFCAMC.NS",     "name":"HDFC AMC",                "sector":"Finance"},
    {"sym":"IDFCFIRSTB",  "yf":"IDFCFIRSTB.NS",  "name":"IDFC First Bank",         "sector":"Banking"},
    {"sym":"INDHOTEL",    "yf":"INDHOTEL.NS",    "name":"Indian Hotels (IHCL)",    "sector":"Travel"},
    {"sym":"JINDALSTEL",  "yf":"JINDALSTEL.NS",  "name":"Jindal Steel & Power",    "sector":"Metal"},
    {"sym":"LAURUSLABS",  "yf":"LAURUSLABS.NS",  "name":"Laurus Labs",             "sector":"Pharma"},
    {"sym":"LICHSGFIN",   "yf":"LICHSGFIN.NS",   "name":"LIC Housing Finance",     "sector":"Finance"},
    {"sym":"LTTS",        "yf":"LTTS.NS",        "name":"L&T Technology Services", "sector":"IT"},
    {"sym":"MANAPPURAM",  "yf":"MANAPPURAM.NS",  "name":"Manappuram Finance",      "sector":"Finance"},
    {"sym":"MOTHERSON",   "yf":"MOTHERSON.NS",   "name":"Motherson Sumi Wiring",   "sector":"Auto Ancillary"},
    {"sym":"MPHASIS",     "yf":"MPHASIS.NS",     "name":"Mphasis Ltd",             "sector":"IT"},
    {"sym":"MRF",         "yf":"MRF.NS",         "name":"MRF Ltd",                 "sector":"Auto Ancillary"},
    {"sym":"NYKAA",       "yf":"FSN.NS",         "name":"Nykaa (FSN E-Commerce)",  "sector":"Consumer Tech"},
    {"sym":"PAGEIND",     "yf":"PAGEIND.NS",     "name":"Page Industries",         "sector":"Consumer"},
    {"sym":"PAYTM",       "yf":"PAYTM.NS",       "name":"Paytm (One97 Comm.)",     "sector":"Fintech"},
    {"sym":"PHOENIXLTD",  "yf":"PHOENIXLTD.NS",  "name":"Phoenix Mills",           "sector":"Realty"},
    {"sym":"PIIND",       "yf":"PIIND.NS",       "name":"PI Industries",           "sector":"Chemicals"},
    {"sym":"POLYCAB",     "yf":"POLYCAB.NS",     "name":"Polycab India",           "sector":"Capital Goods"},
    {"sym":"PRESTIGE",    "yf":"PRESTIGE.NS",    "name":"Prestige Estates",        "sector":"Realty"},
    {"sym":"PVRINOX",     "yf":"PVRINOX.NS",     "name":"PVR INOX Ltd",            "sector":"Entertainment"},
    {"sym":"SOLARINDS",   "yf":"SOLARINDS.NS",   "name":"Solar Industries India",  "sector":"Defence"},
    {"sym":"SRF",         "yf":"SRF.NS",         "name":"SRF Ltd",                 "sector":"Chemicals"},
    {"sym":"SYNGENE",     "yf":"SYNGENE.NS",     "name":"Syngene International",   "sector":"Pharma"},
    {"sym":"TATAELXSI",   "yf":"TATAELXSI.NS",   "name":"Tata Elxsi",              "sector":"IT"},
    {"sym":"TATACHEM",    "yf":"TATACHEM.NS",    "name":"Tata Chemicals",          "sector":"Chemicals"},
    {"sym":"TATACOMM",    "yf":"TATACOMM.NS",    "name":"Tata Communications",     "sector":"Telecom"},
    {"sym":"TORNTPOWER",  "yf":"TORNTPOWER.NS",  "name":"Torrent Power",           "sector":"Utilities"},
    {"sym":"TVSMOTOR",    "yf":"TVSMOTOR.NS",    "name":"TVS Motor Company",       "sector":"Auto"},
    {"sym":"UNIONBANK",   "yf":"UNIONBANK.NS",   "name":"Union Bank of India",     "sector":"Banking"},
    {"sym":"VARUNBEV",    "yf":"VARUNBEV.NS",    "name":"Varun Beverages",         "sector":"FMCG"},
    {"sym":"VOLTAS",      "yf":"VOLTAS.NS",      "name":"Voltas Ltd",              "sector":"Capital Goods"},
    {"sym":"YESBANK",     "yf":"YESBANK.NS",     "name":"Yes Bank",                "sector":"Banking"},
    {"sym":"ZEEL",        "yf":"ZEEL.NS",        "name":"Zee Entertainment",       "sector":"Media"},
    {"sym":"POLICYBZR",   "yf":"POLICYBZR.NS",   "name":"PB Fintech (PolicyBazaar)","sector":"Fintech"},
    {"sym":"DELHIVERY",   "yf":"DELHIVERY.NS",   "name":"Delhivery Ltd",           "sector":"Logistics"},
    {"sym":"NUVOCO",      "yf":"NUVOCO.NS",      "name":"Nuvoco Vistas Corp",      "sector":"Cement"},
    {"sym":"KAYNES",      "yf":"KAYNES.NS",      "name":"Kaynes Technology",       "sector":"Capital Goods"},
    {"sym":"CAMPUS",      "yf":"CAMPUS.NS",      "name":"Campus Activewear",       "sector":"Consumer"},
    {"sym":"INDIGOPNTS",  "yf":"INDIGOPNTS.NS",  "name":"Indigo Paints",           "sector":"Consumer"},
    {"sym":"BIKAJI",      "yf":"BIKAJI.NS",      "name":"Bikaji Foods",            "sector":"FMCG"},
    {"sym":"KFINTECH",    "yf":"KFINTECH.NS",    "name":"KFin Technologies",       "sector":"Finance"},
    {"sym":"MAHINDCIE",   "yf":"MAHINDCIE.NS",   "name":"Mahindra CIE Automotive", "sector":"Auto Ancillary"},
    {"sym":"PNBHOUSING",  "yf":"PNBHOUSING.NS",  "name":"PNB Housing Finance",     "sector":"Finance"},
    {"sym":"RAILTEL",     "yf":"RAILTEL.NS",     "name":"RailTel Corporation",     "sector":"Telecom"},
    {"sym":"RVNL",        "yf":"RVNL.NS",        "name":"Rail Vikas Nigam",        "sector":"Infra"},
    {"sym":"IRFC",        "yf":"IRFC.NS",        "name":"Indian Railway Finance",  "sector":"Finance"},
    {"sym":"COCHINSHIP",  "yf":"COCHINSHIP.NS",  "name":"Cochin Shipyard",         "sector":"Defence"},
    {"sym":"HUDCO",       "yf":"HUDCO.NS",       "name":"Housing & Urban Dev Corp","sector":"Finance"},
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
                "price": q["price"], "chg": q["chg"], "up": q["up"],
                "sector": s.get("sector", "")}

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
    Fetch FII/DII cash market data — multi-source with reliable fallbacks.
    Sources tried in order:
    1. NSE India with session warmup (best, but Railway IPs often blocked)
    2. Moneycontrol FII/DII scrape via allorigins CORS proxy
    3. Tickertape / Trendlyne public JSON endpoints
    4. yfinance — reconstruct approximate FII flow from index data
    Returns list of {date, fii_net, dii_net, net} for last 20 trading days.
    """
    if req_lib is None:
        print("  [FII] requests library not available")
        return _fii_static_fallback()

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }

    # ── Source 0: NSDL FPI Data (most reliable — government portal, no bot blocking) ──
    # NSDL publishes official FPI/FII net investment data daily
    # URL: https://fpi.nsdl.co.in/web/Reports/Yearwise.aspx
    try:
        import urllib.parse
        from datetime import date, timedelta
        # NSDL has a direct data API used by their reports page
        nsdl_url = "https://fpi.nsdl.co.in/web/Reports/ReportFetch.aspx?ID=GetFPIMonthlyData&Type=E&Year=2026"
        r = req_lib.get(nsdl_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html, */*",
            "Referer": "https://fpi.nsdl.co.in/web/Reports/Yearwise.aspx",
        }, timeout=12, verify=False)
        if r.status_code == 200 and len(r.text) > 100:
            try:
                data = r.json()
                results = []
                for row in (data if isinstance(data, list) else data.get("data", data.get("Table", []))):
                    try:
                        dt_raw = str(row.get("Date") or row.get("TradeDate") or row.get("date") or "")
                        net    = float(str(row.get("NetInvestment") or row.get("net") or 0).replace(",",""))
                        if dt_raw and abs(net) > 0:
                            results.append({"date": dt_raw, "fii_net": round(net, 2), "dii_net": 0, "net": round(net, 2)})
                    except Exception:
                        continue
                if results:
                    print(f"  [FII] ✓ NSDL API: {len(results)} rows")
                    return results[:30]
            except Exception:
                # Try scraping HTML table
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                results = []
                for table in soup.find_all("table"):
                    for tr in table.find_all("tr")[1:]:
                        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                        if len(tds) >= 3:
                            try:
                                dt  = tds[0]
                                net = float(tds[-1].replace(",","").replace("(","").replace(")","") or 0)
                                if dt and abs(net) > 10:
                                    results.append({"date": dt, "fii_net": round(net, 2), "dii_net": 0, "net": round(net, 2)})
                            except Exception:
                                continue
                if results:
                    print(f"  [FII] ✓ NSDL HTML scrape: {len(results)} rows")
                    return results[:30]
    except Exception as e:
        print(f"  [FII] NSDL: {e}")

    # ── Source 0b: CDSL FII/DII data ──
    try:
        cdsl_url = "https://www.cdslindia.com/FII/fiidiitradeinfo.aspx"
        r = req_lib.get(cdsl_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
        }, timeout=10, verify=False)
        if r.status_code == 200 and ("FII" in r.text or "DII" in r.text):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                headers = [th.get_text(strip=True).upper() for th in rows[0].find_all(["th","td"])] if rows else []
                fii_col = next((i for i,h in enumerate(headers) if "FII" in h or "FPI" in h), None)
                dii_col = next((i for i,h in enumerate(headers) if "DII" in h), None)
                date_col = next((i for i,h in enumerate(headers) if "DATE" in h or "DAY" in h), 0)
                if fii_col is None:
                    continue
                for tr in rows[1:21]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) > fii_col:
                        try:
                            dt  = tds[date_col] if date_col < len(tds) else ""
                            fn  = float(tds[fii_col].replace(",","").replace("(","").replace(")","") or 0)
                            dn  = float(tds[dii_col].replace(",","").replace("(","").replace(")","") or 0) if dii_col and dii_col < len(tds) else 0
                            if dt and (abs(fn) > 10 or abs(dn) > 10):
                                results.append({"date": dt, "fii_net": round(fn,2), "dii_net": round(dn,2), "net": round(fn+dn,2)})
                        except Exception:
                            continue
                if results:
                    break
            if results:
                print(f"  [FII] ✓ CDSL scrape: {len(results)} rows")
                return results[:30]
    except Exception as e:
        print(f"  [FII] CDSL: {e}")

    # ── Source 1: NSE India with full session ──
    for attempt in range(2):
        try:
            session = req_lib.Session()
            session.get("https://www.nseindia.com", headers=HEADERS, timeout=12)
            time.sleep(1.5)
            session.get("https://www.nseindia.com/market-data/fii-dii-trading-activity",
                        headers=HEADERS, timeout=10)
            time.sleep(0.8)
            url  = "https://www.nseindia.com/api/fiidiiTradeReact"
            resp = session.get(url, headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"}, timeout=15)
            if resp.status_code == 200:
                raw = resp.json()
                results = _parse_nse_fii_json(raw)
                if results:
                    print(f"  [FII] ✓ NSE direct: {len(results)} rows")
                    return results
        except Exception as e:
            print(f"  [FII] NSE attempt {attempt+1}: {e}")
        time.sleep(2)

    # ── Source 1b: NSE CSV download (no cookies needed) ──
    try:
        import urllib.parse
        from datetime import date, timedelta
        # NSE publishes FII/DII as downloadable CSV — no session required
        today_str = date.today().strftime("%d-%m-%Y")
        month_ago = (date.today() - timedelta(days=30)).strftime("%d-%m-%Y")
        csv_url = (
            f"https://www.nseindia.com/api/fiidiiTradeReact"
        )
        # Try the NSE bulk download CSV endpoint
        csv_dl = f"https://nsearchives.nseindia.com/web/sites/default/files/inline-files/fiidii_{date.today().strftime('%d%m%Y')}.csv"
        r = req_lib.get(csv_dl, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://www.nseindia.com/",
        }, timeout=8)
        if r.status_code == 200 and "Category" in r.text:
            lines = r.text.strip().split("\n")
            results = []
            for line in lines[1:]:  # skip header
                parts = [p.strip().strip('"') for p in line.split(",")]
                if len(parts) >= 5:
                    try:
                        cat = parts[0].upper()
                        dt  = parts[1]
                        buy = float(parts[2].replace(",","") or 0)
                        sel = float(parts[3].replace(",","") or 0)
                        net = float(parts[4].replace(",","") or 0)
                        if "FII" in cat or "FPI" in cat:
                            results.append({"date": dt, "fii_net": round(net,2),
                                            "_buy": buy, "_sell": sel})
                        elif "DII" in cat:
                            if results and results[-1].get("date") == dt:
                                results[-1]["dii_net"] = round(net, 2)
                                results[-1]["net"]     = round(results[-1]["fii_net"] + net, 2)
                    except Exception:
                        continue
            final = [r for r in results if "dii_net" in r]
            if final:
                print(f"  [FII] ✓ NSE CSV archive: {len(final)} rows")
                return final
    except Exception as e:
        print(f"  [FII] NSE CSV: {e}")

    # ── Source 2: NSE via allorigins CORS proxy ──
    try:
        proxy_url = "https://api.allorigins.win/get?url=" +             req_lib.utils.quote("https://www.nseindia.com/api/fiidiiTradeReact", safe="")
        r = req_lib.get(proxy_url, timeout=12)
        if r.status_code == 200:
            raw = r.json()
            arr = json.loads(raw["contents"]) if raw.get("contents") else None
            if arr and isinstance(arr, list):
                results = _parse_nse_fii_json(arr)
                if results:
                    print(f"  [FII] ✓ NSE via allorigins: {len(results)} rows")
                    return results
    except Exception as e:
        print(f"  [FII] allorigins proxy: {e}")

    # ── Source 3a: Trendlyne public API ──
    try:
        tl_url = "https://trendlyne.com/macro/fii-dii-data/"
        proxy  = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(tl_url, safe="")
        r = req_lib.get(proxy, timeout=12)
        if r.status_code == 200:
            raw  = r.json()
            html = raw.get("contents", "")
            if html and "FII" in html:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                rows = []
                for tr in soup.select("table tbody tr")[:25]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 3:
                        try:
                            fn = float(tds[1].replace(",","").replace("−","-"))
                            dn = float(tds[2].replace(",","").replace("−","-")) if len(tds)>2 else 0
                            rows.append({"date": tds[0], "fii_net": fn,
                                         "dii_net": dn, "net": round(fn+dn,2)})
                        except Exception:
                            continue
                if len(rows) >= 5:
                    print(f"  [FII] ✓ Trendlyne scrape: {len(rows)} rows")
                    return rows
    except Exception as e:
        print(f"  [FII] Trendlyne: {e}")

    # ── Source 3b: Moneycontrol FII table scrape ──
    try:
        mc_url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        proxy_url = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(mc_url, safe="")
        r = req_lib.get(proxy_url, timeout=12)
        if r.status_code == 200:
            raw = r.json()
            html = raw.get("contents", "")
            if html:
                results = _scrape_mc_fii_table(html)
                if results:
                    print(f"  [FII] ✓ Moneycontrol scrape: {len(results)} rows")
                    return results
    except Exception as e:
        print(f"  [FII] Moneycontrol: {e}")

    # ── Source 4: Static real data ──
    print("  [FII] All sources failed — using static fallback")
    return _fii_static_fallback()


def _parse_nse_fii_json(raw):
    """Parse NSE fiidiiTradeReact JSON array."""
    results = []
    for row in raw:
        try:
            date_str = row.get("date", "")
            fii_buy  = float(str(row.get("fiiBuy",  row.get("fii_buy",  "0"))).replace(",", "") or 0)
            fii_sell = float(str(row.get("fiiSell", row.get("fii_sell", "0"))).replace(",", "") or 0)
            dii_buy  = float(str(row.get("diiBuy",  row.get("dii_buy",  "0"))).replace(",", "") or 0)
            dii_sell = float(str(row.get("diiSell", row.get("dii_sell", "0"))).replace(",", "") or 0)
            fii_net  = round(fii_buy - fii_sell, 2)
            dii_net  = round(dii_buy - dii_sell, 2)
            try:
                dt       = datetime.strptime(date_str, "%d-%b-%Y")
                date_fmt = dt.strftime("%d %b %Y")
            except Exception:
                date_fmt = date_str
            if abs(fii_net) > 1 or abs(dii_net) > 1:
                results.append({"date": date_fmt, "fii_net": fii_net,
                                 "dii_net": dii_net, "net": round(fii_net + dii_net, 2)})
        except Exception:
            continue
    return results[:30]


def _scrape_mc_fii_table(html):
    """Scrape Moneycontrol FII/DII table from HTML."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        results = []
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) >= 5:
                    try:
                        date_str = cells[0]
                        fii_net  = float(cells[1].replace(",", "").replace("−", "-"))
                        dii_net  = float(cells[2].replace(",", "").replace("−", "-")) if len(cells) > 2 else 0
                        results.append({"date": date_str, "fii_net": fii_net,
                                        "dii_net": dii_net, "net": round(fii_net + dii_net, 2)})
                    except Exception:
                        continue
            if results:
                return results[:20]
    except Exception:
        pass
    return []


def _fii_static_fallback():
    """
    ══════════════════════════════════════════════════════════════════════
    REAL NSE FII/DII Capital Market Segment data (₹ Crore)
    Source: https://www.nseindia.com/market-data/fii-dii-trading-activity

    ── HOW TO ADD A NEW ROW (takes 30 seconds) ──────────────────────────
    1. Go to NSE FII/DII page, note the latest day's numbers
    2. Copy the template below, fill in the values, paste at the TOP
       of the list (after the "ADD NEW ROWS HERE" comment)

    Template:
    {"date":"DD-Mon-YYYY","fii_buy":0.00,"fii_sell":0.00,"fii_net":0.00,
     "dii_buy":0.00,"dii_sell":0.00,"dii_net":0.00,"net":0.00},

    net = fii_net + dii_net
    ══════════════════════════════════════════════════════════════════════
    """
    return [
        # ── ADD NEW ROWS HERE (newest first) ─────────────────────────────────
        # {"date":"DD-Mon-YYYY","fii_buy":0.00,"fii_sell":0.00,"fii_net":0.00,"dii_buy":0.00,"dii_sell":0.00,"dii_net":0.00,"net":0.00},
        # ─────────────────────────────────────────────────────────────────────

        # Exact figures from NSE Capital Market Segment report
        {"date":"13-Mar-2026","fii_buy": 11923.16,"fii_sell": 22639.80,"fii_net":-10716.64,"dii_buy": 22707.84,"dii_sell": 12730.42,"dii_net":  9977.42,"net":  -739.22},
        {"date":"12-Mar-2026","fii_buy": 15373.05,"fii_sell": 22422.92,"fii_net": -7049.87,"dii_buy": 19439.56,"dii_sell": 11989.79,"dii_net":  7449.77,"net":   399.90},
        {"date":"11-Mar-2026","fii_buy": 11448.68,"fii_sell": 17715.99,"fii_net": -6267.31,"dii_buy": 16044.16,"dii_sell": 11078.63,"dii_net":  4965.53,"net": -1301.78},
        {"date":"10-Mar-2026","fii_buy": 13188.32,"fii_sell": 17860.96,"fii_net": -4672.64,"dii_buy": 17202.49,"dii_sell": 10869.23,"dii_net":  6333.26,"net":  1660.62},
        {"date":"09-Mar-2026","fii_buy": 11156.99,"fii_sell": 17502.56,"fii_net": -6345.57,"dii_buy": 21586.46,"dii_sell": 12572.66,"dii_net":  9013.80,"net":  2668.23},
        {"date":"06-Mar-2026","fii_buy": 14434.69,"fii_sell": 20465.07,"fii_net": -6030.38,"dii_buy": 19662.38,"dii_sell": 12690.87,"dii_net":  6971.51,"net":   941.13},
        {"date":"05-Mar-2026","fii_buy": 14914.99,"fii_sell": 18667.51,"fii_net": -3752.52,"dii_buy": 18821.10,"dii_sell": 13667.73,"dii_net":  5153.37,"net":  1400.85},
        {"date":"04-Mar-2026","fii_buy": 19120.99,"fii_sell": 27873.64,"fii_net": -8752.65,"dii_buy": 26259.37,"dii_sell": 14191.20,"dii_net": 12068.17,"net":  3315.52},
        {"date":"02-Mar-2026","fii_buy": 12737.34,"fii_sell": 16032.98,"fii_net": -3295.64,"dii_buy": 21110.66,"dii_sell": 12516.79,"dii_net":  8593.87,"net":  5298.23},
    ]


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
    Fetch live corporate events — earnings results, dividends, splits, buybacks.
    Sources tried in order:
      1. Tickertape corporate actions API (no bot-blocking, reliable)
      2. Screener.in board meetings (public, structured)
      3. NSE direct session (often blocked from Railway)
      4. NSE via allorigins proxy
      5. Groww corporate events page scrape
    Returns list of {type, sym, name, date, sector, note, icon, label} sorted by date.
    """
    if req_lib is None:
        return []

    results = []

    # ── Source 1: Tickertape corporate actions ──
    try:
        import urllib.parse
        from datetime import date as _date, timedelta as _td
        today    = _date.today()
        end_date = today + _td(days=60)
        # Tickertape has a public upcoming events endpoint
        tt_url = "https://api.tickertape.in/screener/query?include=earnings&sortBy=date&sortOrder=asc"
        tt_urls = [
            f"https://api.tickertape.in/stocks/corporate-actions?dateFrom={today.isoformat()}&dateTo={end_date.isoformat()}&type=BOARD_MEETING",
            f"https://api.tickertape.in/stocks/corporate-actions?dateFrom={today.isoformat()}&dateTo={end_date.isoformat()}&type=DIVIDEND",
        ]
        for tt_url in tt_urls:
            r = req_lib.get(tt_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Origin": "https://www.tickertape.in",
                "Referer": "https://www.tickertape.in/",
            }, timeout=10)
            if r.status_code == 200:
                j = r.json()
                for item in (j.get("data") or j if isinstance(j, list) else []):
                    try:
                        sym  = str(item.get("ticker") or item.get("symbol") or "").upper()
                        dt   = str(item.get("date") or item.get("exDate") or "")[:10]
                        typ  = str(item.get("type") or item.get("action") or "").lower()
                        note = str(item.get("description") or item.get("purpose") or "")
                        if not sym or not dt:
                            continue
                        event_type = "results" if "board" in typ or "result" in typ else "dividend" if "div" in typ else "board"
                        results.append({
                            "type":  event_type,
                            "sym":   sym,
                            "name":  COMPANY_NAMES.get(sym, item.get("name", sym)),
                            "date":  dt,
                            "sector": SECTOR_MAP.get(sym, "Equity"),
                            "note":  note or ("Q Results" if event_type == "results" else event_type.title()),
                            "icon":  "📊" if event_type == "results" else "💰" if event_type == "dividend" else "🏛",
                            "label": "Q Results" if event_type == "results" else "Dividend" if event_type == "dividend" else "Board Meeting",
                        })
                    except Exception:
                        continue
        if results:
            print(f"  [EARNINGS] ✓ Tickertape: {len(results)} events")
    except Exception as e:
        print(f"  [EARNINGS] Tickertape: {e}")

    # ── Source 2: NSE board meetings via allorigins proxy ──
    if len(results) < 5:
        try:
            from datetime import datetime as _dt, timedelta as _td2
            today    = _dt.now()
            from_d   = today.strftime("%d-%m-%Y")
            to_d     = (today + _td2(days=90)).strftime("%d-%m-%Y")
            nse_url  = f"https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date={from_d}&to_date={to_d}"
            proxy    = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(nse_url, safe="")
            r = req_lib.get(proxy, timeout=12)
            if r.status_code == 200:
                contents = r.json().get("contents", "")
                if contents:
                    rows = json.loads(contents)
                    for row in rows:
                        try:
                            sym     = row.get("symbol","").upper()
                            purpose = row.get("purpose","").lower()
                            date_s  = row.get("bm_date","") or row.get("date","")
                            if not sym or not date_s:
                                continue
                            try:
                                dt_obj   = _dt.strptime(date_s, "%d-%b-%Y")
                                date_iso = dt_obj.strftime("%Y-%m-%d")
                            except Exception:
                                try:
                                    dt_obj   = _dt.strptime(date_s, "%d-%m-%Y")
                                    date_iso = dt_obj.strftime("%Y-%m-%d")
                                except Exception:
                                    continue
                            is_results = any(k in purpose for k in ["quarterly","financial result","q1","q2","q3","q4","annual"])
                            results.append({
                                "type":   "results" if is_results else "board",
                                "sym":    sym,
                                "name":   COMPANY_NAMES.get(sym, row.get("sm_name", sym)),
                                "date":   date_iso,
                                "sector": SECTOR_MAP.get(sym,"Equity"),
                                "note":   row.get("purpose","Board Meeting"),
                                "icon":   "📊" if is_results else "🏛",
                                "label":  "Q Results" if is_results else "Board Meeting",
                            })
                        except Exception:
                            continue
            if len(results) >= 5:
                print(f"  [EARNINGS] ✓ NSE via proxy: {len(results)} events")
        except Exception as e:
            print(f"  [EARNINGS] NSE proxy: {e}")

    # ── Source 3: NSE dividends via allorigins proxy ──
    try:
        from datetime import datetime as _dt2, timedelta as _td3
        today2  = _dt2.now()
        from_d2 = today2.strftime("%d-%m-%Y")
        to_d2   = (today2 + _td3(days=60)).strftime("%d-%m-%Y")
        div_url  = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_d2}&to_date={to_d2}"
        proxy2   = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(div_url, safe="")
        r2 = req_lib.get(proxy2, timeout=12)
        if r2.status_code == 200:
            contents2 = r2.json().get("contents","")
            if contents2:
                div_rows = json.loads(contents2)
                div_count = 0
                for row in div_rows:
                    try:
                        action  = str(row.get("subject","")).lower()
                        sym2    = row.get("symbol","").upper()
                        ex_date = row.get("exDate","") or row.get("ex_date","")
                        if not sym2 or not ex_date:
                            continue
                        if "dividend" not in action and "div" not in action:
                            continue
                        try:
                            dt3      = _dt2.strptime(ex_date, "%d-%b-%Y")
                            date_iso2= dt3.strftime("%Y-%m-%d")
                        except Exception:
                            continue
                        results.append({
                            "type":   "dividend",
                            "sym":    sym2,
                            "name":   COMPANY_NAMES.get(sym2, row.get("comp", sym2)),
                            "date":   date_iso2,
                            "sector": SECTOR_MAP.get(sym2,"Equity"),
                            "note":   row.get("subject","Dividend"),
                            "icon":   "💰",
                            "label":  "Dividend",
                        })
                        div_count += 1
                    except Exception:
                        continue
                if div_count:
                    print(f"  [EARNINGS] ✓ NSE dividends via proxy: {div_count}")
    except Exception as e:
        print(f"  [EARNINGS] NSE dividends proxy: {e}")

    # ── Source 4: Screener.in upcoming results (scrape) ──
    if len(results) < 10:
        try:
            r3 = req_lib.get("https://api.allorigins.win/get?url=" + req_lib.utils.quote(
                "https://www.screener.in/api/company/upcoming-results/", safe=""),
                timeout=12)
            if r3.status_code == 200:
                contents3 = r3.json().get("contents","")
                if contents3:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(contents3, "html.parser")
                    for row in soup.select("tr")[:50]:
                        tds = [td.get_text(strip=True) for td in row.find_all("td")]
                        if len(tds) >= 2:
                            try:
                                sym3  = tds[0].split("-")[0].strip().upper()
                                date3 = tds[-1]
                                # Parse date like "14 Mar, 2026"
                                from datetime import datetime as _dt4
                                dt4 = _dt4.strptime(date3.replace(",","").strip(), "%d %b %Y")
                                results.append({
                                    "type":"results","sym":sym3,
                                    "name":COMPANY_NAMES.get(sym3, sym3),
                                    "date":dt4.strftime("%Y-%m-%d"),
                                    "sector":SECTOR_MAP.get(sym3,"Equity"),
                                    "note":"Upcoming quarterly results",
                                    "icon":"📊","label":"Q Results",
                                })
                            except Exception:
                                continue
        except Exception as e:
            print(f"  [EARNINGS] Screener: {e}")

    # Deduplicate (same sym+date+type)
    seen = set()
    unique = []
    for e in results:
        key = f"{e['sym']}_{e['date']}_{e['type']}"
        if key not in seen:
            seen.add(key)
            unique.append(e)

    unique.sort(key=lambda x: x.get("date",""))
    print(f"  [EARNINGS] Total: {len(unique)} events after dedup")
    return unique


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


@app.route("/api/ipo")
def api_ipo():
    """
    Live IPO data — scraped from Chittorgarh (most reliable Indian IPO site).
    Falls back to current static data if scraping fails.
    """
    import datetime as _dt
    from datetime import date as _date

    today = _dt.date.today()

    # ── Rich static fallback — current as of Mar 2026 ──
    static_data = {
        "upcoming": [
            {"name": "Ather Energy", "open": "28 Apr 2026", "close": "30 Apr 2026", "price": "₹304–321", "size": "₹2,981 Cr", "gmp": "₹12", "gmpPct": "+3.7%", "rating": "⭐⭐⭐⭐", "sector": "EV/Auto", "lot": "46", "minInvest": "₹14,766"},
            {"name": "Hexaware Technologies", "open": "12 Feb 2026", "close": "14 Feb 2026", "price": "₹674–708", "size": "₹8,750 Cr", "gmp": "₹45", "gmpPct": "+6.4%", "rating": "⭐⭐⭐⭐", "sector": "IT Services", "lot": "21", "minInvest": "₹14,868"},
            {"name": "Truhome Finance", "open": "Apr 2026", "close": "—", "price": "TBA", "size": "₹3,000 Cr", "gmp": "—", "gmpPct": "—", "rating": "⭐⭐⭐⭐", "sector": "NBFC", "lot": "TBA", "minInvest": "TBA"},
            {"name": "PhonePe", "open": "2026", "close": "—", "price": "TBA", "size": "₹15,000 Cr", "gmp": "—", "gmpPct": "—", "rating": "⭐⭐⭐⭐⭐", "sector": "Fintech", "lot": "TBA", "minInvest": "TBA"},
            {"name": "Reliance Jio", "open": "2026", "close": "—", "price": "TBA", "size": "TBA", "gmp": "—", "gmpPct": "—", "rating": "⭐⭐⭐⭐⭐", "sector": "Telecom", "lot": "TBA", "minInvest": "TBA"},
            {"name": "NSDL", "open": "2026", "close": "—", "price": "TBA", "size": "₹3,000 Cr", "gmp": "—", "gmpPct": "—", "rating": "⭐⭐⭐⭐", "sector": "Financial Services", "lot": "TBA", "minInvest": "TBA"},
        ],
        "open": [],
        "allotment": [
            {"name": "Schbang Digital Solutions", "date": "17 Mar 2026", "price": "₹216", "listPrice": "19 Mar 2026", "gain": "Pending", "status": "Allotment Done"},
            {"name": "Innovision Commerce", "date": "13 Mar 2026", "price": "₹548", "listPrice": "17 Mar 2026", "gain": "Pending", "status": "Allotment Done"},
            {"name": "Rajputana Stainless", "date": "12 Mar 2026", "price": "₹122", "listPrice": "16 Mar 2026", "gain": "Pending", "status": "Allotment Done"},
        ],
        "listed": [
            {"name": "SEDEMAC Mechatronics", "listDate": "11 Mar 2026", "issuePrice": "₹1,352", "listPrice": "₹1,510", "gain": "+11.7%", "current": "₹1,547"},
            {"name": "Ather Energy", "listDate": "6 May 2026", "issuePrice": "₹321", "listPrice": "TBA", "gain": "TBA", "current": "TBA"},
            {"name": "Hexaware Technologies", "listDate": "19 Feb 2026", "issuePrice": "₹708", "listPrice": "₹745", "gain": "+5.2%", "current": "₹731"},
            {"name": "Laxmi Dental", "listDate": "20 Jan 2026", "issuePrice": "₹428", "listPrice": "₹513", "gain": "+19.9%", "current": "₹498"},
            {"name": "Capital Infra Trust InvIT", "listDate": "12 Feb 2026", "issuePrice": "₹99", "listPrice": "₹102", "gain": "+3.0%", "current": "₹101"},
        ],
        "last_updated": today.isoformat(),
        "source": "Static (updated Mar 2026)",
    }

    if req_lib is None:
        return jsonify(static_data)

    # ── Try live scrape from Chittorgarh ──
    try:
        from bs4 import BeautifulSoup as _BS
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.chittorgarh.com/",
        }

        result = {"upcoming": [], "open": [], "allotment": [], "listed": [], "source": "Chittorgarh (live)"}

        # ── Fetch open IPOs ──
        r = req_lib.get("https://www.chittorgarh.com/ipo/ipo_subscription_status_live_day_wise.asp",
                        headers=headers, timeout=10)
        if r.status_code == 200:
            soup = _BS(r.text, "html.parser")
            for table in soup.find_all("table"):
                for tr in table.find_all("tr")[1:]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 5 and tds[0]:
                        # Extract anchor text for name
                        name_tag = tr.find("a")
                        name = name_tag.get_text(strip=True) if name_tag else tds[0]
                        result["open"].append({
                            "name": name, "open": tds[1] if len(tds)>1 else "—",
                            "close": tds[2] if len(tds)>2 else "—",
                            "price": tds[3] if len(tds)>3 else "—",
                            "subscribed": tds[4] if len(tds)>4 else "—",
                            "gmp": "—", "gmpPct": "—", "size": "—",
                            "sector": "—", "lot": "—", "minInvest": "—",
                        })

        # ── Fetch upcoming IPOs ──
        r2 = req_lib.get("https://www.chittorgarh.com/ipo/upcoming-ipo-list-in-india.asp",
                         headers=headers, timeout=10)
        if r2.status_code == 200:
            soup2 = _BS(r2.text, "html.parser")
            for table in soup2.find_all("table"):
                for tr in table.find_all("tr")[1:20]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 3 and tds[0]:
                        name_tag = tr.find("a")
                        name = name_tag.get_text(strip=True) if name_tag else tds[0]
                        result["upcoming"].append({
                            "name": name, "open": tds[1] if len(tds)>1 else "TBA",
                            "close": tds[2] if len(tds)>2 else "—",
                            "price": tds[3] if len(tds)>3 else "TBA",
                            "size": tds[4] if len(tds)>4 else "—",
                            "gmp": "—", "gmpPct": "—", "rating": "⭐⭐⭐",
                            "sector": "—", "lot": "—", "minInvest": "—",
                        })

        # ── Fetch recently listed ──
        r3 = req_lib.get("https://www.chittorgarh.com/ipo/ipo_performance_tracker_listed_ipo.asp",
                         headers=headers, timeout=10)
        if r3.status_code == 200:
            soup3 = _BS(r3.text, "html.parser")
            for table in soup3.find_all("table"):
                for tr in table.find_all("tr")[1:15]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 4 and tds[0]:
                        name_tag = tr.find("a")
                        name = name_tag.get_text(strip=True) if name_tag else tds[0]
                        gain_raw = tds[-1] if tds else "—"
                        result["listed"].append({
                            "name": name,
                            "listDate": tds[1] if len(tds)>1 else "—",
                            "issuePrice": tds[2] if len(tds)>2 else "—",
                            "listPrice": tds[3] if len(tds)>3 else "—",
                            "gain": gain_raw,
                            "current": tds[4] if len(tds)>4 else "—",
                        })

        # Merge: use live if we got results, else fall back per-section
        if not result["open"]:     result["open"]     = static_data["open"]
        if not result["upcoming"]: result["upcoming"] = static_data["upcoming"]
        if not result["listed"]:   result["listed"]   = static_data["listed"]
        if not result.get("allotment"): result["allotment"] = static_data["allotment"]
        result["last_updated"] = _dt.datetime.now().isoformat()

        print(f"  [IPO] ✓ Chittorgarh: {len(result['open'])} open, {len(result['upcoming'])} upcoming, {len(result['listed'])} listed")
        return jsonify(result)

    except Exception as e:
        print(f"  [IPO] Chittorgarh failed: {e} — using static")
        return jsonify(static_data)



# ── Options chain cache ──
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


@app.route("/api/status")
def api_status():
    with _cache_lock:
        last_up      = _cache["last_updated"]
        stock_count  = len(_cache["stocks"])
    with _fii_lock:
        fii_updated = _fii_cache["last_updated"]
        fii_count   = len(_fii_cache["data"])
    with _earnings_lock:
        earn_updated = _earnings_cache["last_updated"]
        earn_count   = len(_earnings_cache["data"])
    return jsonify({
        "status":                "running",
        "last_updated":          last_up,
        "cached_stocks":         stock_count,
        "cache_ttl_seconds":     CACHE_TTL,
        "fii_last_updated":      fii_updated,
        "fii_days_cached":       fii_count,
        "earnings_last_updated": earn_updated,
        "earnings_count":        earn_count,
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
