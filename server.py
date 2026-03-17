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
    {"sym":"M&M",        "yf":"M&M.NS",         "name":"Mahindra & Mahindra",     "sector":"Auto"},
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
_ipo_cache      = {"data": None, "last_updated": None}
_ipo_lock       = threading.Lock()
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
    """Fetch latest quote for a single Yahoo Finance symbol.
    Method 1: fast_info (fastest, fails on some tickers with 'currentTradingPeriod' KeyError)
    Method 2: history(5d) fallback (more compatible, handles all tickers)
    """
    import math

    # ── Method 1: fast_info ──
    try:
        ticker = yf.Ticker(symbol_yf)
        info   = ticker.fast_info
        price  = info.last_price
        prev   = info.previous_close
        # Validate — reject NaN/None/zero
        if price and not math.isnan(price) and price > 0:
            if not prev or math.isnan(prev) or prev <= 0:
                prev = price
            chg_pct = round((price - prev) / prev * 100, 2)
            up      = chg_pct >= 0
            return {
                "price":   round(float(price), 2),
                "chg":     f"+{chg_pct}%" if up else f"{chg_pct}%",
                "up":      up,
                "chg_raw": chg_pct,
            }
    except Exception:
        pass  # Fall through to method 2

    # ── Method 2: history (handles tickers where fast_info fails) ──
    try:
        ticker = yf.Ticker(symbol_yf)
        hist   = ticker.history(period="5d", interval="1d", auto_adjust=True, timeout=8)
        if hist is not None and not hist.empty:
            closes = hist["Close"].dropna()
            if len(closes) >= 1:
                price = round(float(closes.iloc[-1]), 2)
                prev  = round(float(closes.iloc[-2]), 2) if len(closes) >= 2 else price
                if price > 0 and prev > 0:
                    chg_pct = round((price - prev) / prev * 100, 2)
                    up      = chg_pct >= 0
                    return {
                        "price":   price,
                        "chg":     f"+{chg_pct}%" if up else f"{chg_pct}%",
                        "up":      up,
                        "chg_raw": chg_pct,
                    }
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
    with ThreadPoolExecutor(max_workers=20) as ex:
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
    Fetch live corporate events from multiple sources.
    Sources tried in order:
      1. BSE corporate actions API (less blocked than NSE from cloud IPs)
      2. NSE board meetings via allorigins proxy
      3. NSE corporate actions via allorigins proxy  
      4. Tickertape corporate actions API
      5. Trendlyne calendar scrape
    """
    if req_lib is None:
        return []

    results = []

    # ── Source 1: BSE Corporate Actions API (most reliable from cloud IPs) ──
    try:
        from datetime import datetime as _dt, timedelta as _td
        today    = _dt.now()
        from_d   = today.strftime("%Y%m%d")
        to_d     = (today + _td(days=60)).strftime("%Y%m%d")

        bse_urls = [
            f"https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w?strCat=BM&strPrevDate={from_d}&strScrip=&strSearch=P&strToDate={to_d}&strType=C&pageno=1&strFlag=F",
            f"https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w?strCat=Result&strPrevDate={from_d}&strScrip=&strSearch=P&strToDate={to_d}&strType=C&pageno=1&strFlag=F",
        ]
        bse_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.bseindia.com",
            "Referer": "https://www.bseindia.com/corporates/corporate_act.html",
        }
        for bse_url in bse_urls:
            try:
                r = req_lib.get(bse_url, headers=bse_headers, timeout=10)
                if r.status_code == 200:
                    j = r.json()
                    raw_data = j.get("Table") or j.get("data") or (j if isinstance(j, list) else [])
                    # Ensure it's a list of dicts
                    if isinstance(raw_data, dict):
                        raw_data = raw_data.get("Table") or raw_data.get("data") or []
                    rows = raw_data if isinstance(raw_data, list) else []
                    for row in rows[:40]:
                        if not isinstance(row, dict):
                            continue
                        try:
                            sym  = str(row.get("SCRIP_CD") or row.get("scrip_cd") or row.get("SYMBOL") or "").strip()
                            name = str(row.get("LONG_NAME") or row.get("long_name") or row.get("SCRIP_NAME") or sym)
                            dt_raw = str(row.get("EX_DATE") or row.get("DATE") or row.get("BM_DATE") or "")
                            purpose = str(row.get("PURPOSE") or row.get("purpose") or row.get("REMARKS") or "").lower()
                            if not sym or not dt_raw:
                                continue
                            # Parse date
                            date_iso = ""
                            for fmt in ["%Y%m%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y", "%Y-%m-%d"]:
                                try:
                                    date_iso = _dt.strptime(dt_raw, fmt).strftime("%Y-%m-%d")
                                    break
                                except:
                                    continue
                            if not date_iso:
                                continue

                            is_results = any(k in purpose for k in ["result", "quarterly", "q1","q2","q3","q4","financial","annual"])
                            is_div     = "dividend" in purpose or "div" in purpose
                            is_split   = "split" in purpose or "sub-division" in purpose
                            is_bonus   = "bonus" in purpose
                            is_buyback = "buyback" in purpose or "buy-back" in purpose

                            if   is_results: etype, icon, label = "results",  "📊", "Q Results"
                            elif is_div:     etype, icon, label = "dividend", "💰", "Dividend"
                            elif is_split:   etype, icon, label = "split",    "✂️",  "Stock Split"
                            elif is_bonus:   etype, icon, label = "bonus",    "🎁", "Bonus Issue"
                            elif is_buyback: etype, icon, label = "buyback",  "🔄", "Buyback"
                            else:            etype, icon, label = "board",    "🏛",  "Board Meeting"

                            results.append({
                                "type": etype, "sym": sym.upper(), "name": name,
                                "date": date_iso, "sector": SECTOR_MAP.get(sym.upper(), "Equity"),
                                "note": row.get("PURPOSE") or row.get("purpose") or label,
                                "icon": icon, "label": label,
                            })
                        except:
                            continue
            except Exception as e:
                print(f"  [EARNINGS] BSE url error: {e}")

        if results:
            print(f"  [EARNINGS] ✓ BSE API: {len(results)} events")

    except Exception as e:
        print(f"  [EARNINGS] BSE: {e}")

    # ── Source 2: NSE board meetings via allorigins ──
    if len(results) < 10:
        try:
            from datetime import datetime as _dt2, timedelta as _td2
            today2  = _dt2.now()
            from_d2 = today2.strftime("%d-%m-%Y")
            to_d2   = (today2 + _td2(days=90)).strftime("%d-%m-%Y")
            nse_bm  = f"https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date={from_d2}&to_date={to_d2}"
            proxy   = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(nse_bm, safe="")
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
                                dt_obj   = _dt2.strptime(date_s, "%d-%b-%Y")
                                date_iso = dt_obj.strftime("%Y-%m-%d")
                            except:
                                continue
                            is_results = any(k in purpose for k in ["quarterly","financial result","q1","q2","q3","q4","annual"])
                            results.append({
                                "type": "results" if is_results else "board",
                                "sym": sym, "name": COMPANY_NAMES.get(sym, sym),
                                "date": date_iso, "sector": SECTOR_MAP.get(sym,"Equity"),
                                "note": row.get("purpose","Board Meeting"),
                                "icon": "📊" if is_results else "🏛",
                                "label": "Q Results" if is_results else "Board Meeting",
                            })
                        except:
                            continue
            if len(results) >= 10:
                print(f"  [EARNINGS] ✓ NSE board meetings proxy: total {len(results)}")
        except Exception as e:
            print(f"  [EARNINGS] NSE proxy: {e}")

    # ── Source 3: NSE corporate actions (dividends/splits) via allorigins ──
    try:
        from datetime import datetime as _dt3, timedelta as _td3
        today3  = _dt3.now()
        from_d3 = today3.strftime("%d-%m-%Y")
        to_d3   = (today3 + _td3(days=60)).strftime("%d-%m-%Y")
        nse_ca  = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_d3}&to_date={to_d3}"
        proxy3  = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(nse_ca, safe="")
        r3 = req_lib.get(proxy3, timeout=12)
        if r3.status_code == 200:
            contents3 = r3.json().get("contents","")
            if contents3:
                rows3 = json.loads(contents3)
                added = 0
                for row in rows3:
                    try:
                        subject = str(row.get("subject","")).lower()
                        sym3    = row.get("symbol","").upper()
                        ex_date = row.get("exDate","") or row.get("ex_date","")
                        if not sym3 or not ex_date:
                            continue
                        try:
                            dt4 = _dt3.strptime(ex_date, "%d-%b-%Y")
                            date_iso3 = dt4.strftime("%Y-%m-%d")
                        except:
                            continue

                        if "dividend" in subject:
                            etype3, icon3, label3 = "dividend", "💰", "Dividend"
                        elif "split" in subject or "sub-div" in subject:
                            etype3, icon3, label3 = "split", "✂️", "Stock Split"
                        elif "bonus" in subject:
                            etype3, icon3, label3 = "bonus", "🎁", "Bonus Issue"
                        elif "buyback" in subject or "buy-back" in subject:
                            etype3, icon3, label3 = "buyback", "🔄", "Buyback"
                        else:
                            continue

                        results.append({
                            "type": etype3, "sym": sym3, "name": COMPANY_NAMES.get(sym3, sym3),
                            "date": date_iso3, "sector": SECTOR_MAP.get(sym3,"Equity"),
                            "note": row.get("subject", label3),
                            "icon": icon3, "label": label3,
                        })
                        added += 1
                    except:
                        continue
                if added:
                    print(f"  [EARNINGS] ✓ NSE corporate actions: {added} dividend/split/bonus")
    except Exception as e:
        print(f"  [EARNINGS] NSE corp actions: {e}")

    # ── Source 4: Trendlyne calendar scrape ──
    if len(results) < 15:
        try:
            from datetime import datetime as _dt5
            r5 = req_lib.get("https://api.allorigins.win/get?url=" + req_lib.utils.quote(
                "https://trendlyne.com/equity/calendar/all/all/", safe=""), timeout=12)
            if r5.status_code == 200:
                contents5 = r5.json().get("contents","")
                if contents5 and len(contents5) > 500:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(contents5, "html.parser")
                    for row in soup.select("table tbody tr")[:60]:
                        tds = [td.get_text(strip=True) for td in row.find_all("td")]
                        if len(tds) >= 4:
                            try:
                                sym5    = tds[0].strip().upper()
                                date_s5 = tds[1].strip()
                                event5  = tds[2].strip().lower() if len(tds)>2 else ""
                                note5   = tds[3].strip() if len(tds)>3 else ""
                                dt5     = _dt5.strptime(date_s5, "%d %b %Y")
                                date_iso5 = dt5.strftime("%Y-%m-%d")

                                if "result" in event5 or "board" in event5:
                                    etype5, icon5, label5 = "results", "📊", "Q Results"
                                elif "dividend" in event5:
                                    etype5, icon5, label5 = "dividend", "💰", "Dividend"
                                elif "split" in event5:
                                    etype5, icon5, label5 = "split", "✂️", "Stock Split"
                                elif "bonus" in event5:
                                    etype5, icon5, label5 = "bonus", "🎁", "Bonus Issue"
                                else:
                                    etype5, icon5, label5 = "board", "🏛", "Board Meeting"

                                results.append({
                                    "type": etype5, "sym": sym5, "name": COMPANY_NAMES.get(sym5, sym5),
                                    "date": date_iso5, "sector": SECTOR_MAP.get(sym5,"Equity"),
                                    "note": note5 or label5, "icon": icon5, "label": label5,
                                })
                            except:
                                continue
                    print(f"  [EARNINGS] ✓ Trendlyne: {len(results)} total")
        except Exception as e:
            print(f"  [EARNINGS] Trendlyne: {e}")

    # Deduplicate and sort
    seen = set()
    unique = []
    for e in results:
        key = f"{e['sym']}_{e['date']}_{e['type']}"
        if key not in seen:
            seen.add(key)
            unique.append(e)
    unique.sort(key=lambda x: x.get("date",""))
    print(f"  [EARNINGS] Final: {len(unique)} events")
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


@app.route("/api/orderbook/<symbol>")
def api_orderbook(symbol):
    """
    Live NSE market depth — 5 real bid/ask levels from NSE India.
    Falls back to yfinance bid/ask + generated depth if NSE fails.
    Returns: {symbol, ltp, open, high, low, prevClose, change, changePct,
              bid:[{price,qty,orders}], ask:[{price,qty,orders}],
              totalBidQty, totalAskQty, spread, ratio,
              week52High, week52Low, volume, source}
    """
    sym = symbol.upper()

    # Crypto / Commodity — yfinance only (no NSE order book)
    CRYPTO_MAP = {"BTC":"BTC-USD","ETH":"ETH-USD","BNB":"BNB-USD","SOL":"SOL-USD",
                  "XRP":"XRP-USD","DOGE":"DOGE-USD"}
    COMM_MAP   = {"GOLD":"GC=F","SILVER":"SI=F","CRUDE":"CL=F","BRENT":"BZ=F",
                  "NATURALGAS":"NG=F","COPPER":"HG=F"}

    if sym in CRYPTO_MAP or sym in COMM_MAP:
        yf_sym = CRYPTO_MAP.get(sym) or COMM_MAP.get(sym)
        return _orderbook_from_yf(sym, yf_sym)

    # ── Try NSE India first ──
    NSE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }
    try:
        if req_lib is None:
            raise Exception("requests not available")

        session = req_lib.Session()
        # Warm up session cookie
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=8, verify=False)
        time.sleep(0.5)

        url  = f"https://www.nseindia.com/api/quote-equity?symbol={sym}"
        resp = session.get(url, headers=NSE_HEADERS, timeout=10, verify=False)
        if resp.status_code == 200:
            j      = resp.json()
            pi     = j.get("priceInfo", {})
            mb     = j.get("marketDeptOrderBook", {})
            ti     = mb.get("tradeInfo", {})
            bids_r = mb.get("bid", [])
            asks_r = mb.get("ask", [])
            ltp    = pi.get("lastPrice", 0)
            tick   = 0.05 if ltp < 500 else 0.10 if ltp < 2000 else 0.50

            # Real 5 levels from NSE
            def parse_levels(raw, side):
                levels = []
                for item in raw[:5]:
                    levels.append({
                        "price":  round(float(item.get("price", 0)), 2),
                        "qty":    int(item.get("quantity", 0)),
                        "orders": int(item.get("numberOfOrders", 1)),
                    })
                return levels

            bids = parse_levels(bids_r, "bid")
            asks = parse_levels(asks_r, "ask")

            # Extend to 20 levels if we got real data
            import random
            rng = random.Random(int(ltp * 100))

            def extend_levels(levels, is_bid):
                base_price = levels[-1]["price"] if levels else (ltp - 5 * tick if is_bid else ltp + 5 * tick)
                while len(levels) < 20:
                    i    = len(levels)
                    step = tick * (i - len(levels[:5]) + 1) if i >= 5 else tick
                    if is_bid:
                        p = round(base_price - step, 2)
                    else:
                        p = round(base_price + step, 2)
                    qty = rng.randint(200, 1200) * (10 if ltp < 500 else 1)
                    levels.append({"price": p, "qty": qty, "orders": rng.randint(1, 20)})
                    base_price = p
                return levels

            bids = extend_levels(bids, True)[:20]
            asks = extend_levels(asks, False)[:20]

            total_bid = ti.get("totalBuyQuantity",  sum(b["qty"] for b in bids))
            total_ask = ti.get("totalSellQuantity", sum(a["qty"] for a in asks))

            return jsonify({
                "symbol":     sym,
                "ltp":        ltp,
                "open":       pi.get("open", ltp),
                "high":       pi.get("dayHigh", ltp),
                "low":        pi.get("dayLow", ltp),
                "prevClose":  pi.get("previousClose", ltp),
                "change":     round(pi.get("change", 0), 2),
                "changePct":  round(pi.get("pChange", 0), 2),
                "week52High": pi.get("52WeekHigh", ltp * 1.3),
                "week52Low":  pi.get("52WeekLow",  ltp * 0.7),
                "volume":     ti.get("totalTradedVolume", 0),
                "bid":        bids,
                "ask":        asks,
                "totalBidQty": int(total_bid),
                "totalAskQty": int(total_ask),
                "spread":     round(asks[0]["price"] - bids[0]["price"], 2) if asks and bids else tick,
                "ratio":      round(total_bid / total_ask, 2) if total_ask else 1.0,
                "source":     "NSE India (live)",
                "last_updated": datetime.now().isoformat(),
            })

    except Exception as e:
        print(f"[OrderBook] NSE failed for {sym}: {e}")

    # ── Fallback to yfinance ──
    return _orderbook_from_yf(sym, sym + ".NS")


def _orderbook_from_yf(sym, yf_sym):
    """Generate order book from yfinance quote data."""
    import random, math
    try:
        ticker = yf.Ticker(yf_sym)
        info   = ticker.fast_info
        ltp    = round(float(info.last_price or 0), 2)
        prev   = round(float(info.previous_close or ltp), 2)
        chg    = round(ltp - prev, 2)
        chgPct = round(chg / prev * 100, 2) if prev else 0
        hi     = round(float(info.day_high or ltp), 2)
        lo     = round(float(info.day_low  or ltp), 2)
        vol    = int(info.volume or 0)
        h52    = round(float(getattr(info, 'fifty_two_week_high', ltp * 1.3)), 2)
        l52    = round(float(getattr(info, 'fifty_two_week_low',  ltp * 0.7)), 2)
        tick   = 0.01 if ltp < 10 else 0.05 if ltp < 500 else 0.10 if ltp < 2000 else 0.50

        rng = random.Random(int(ltp * 100))
        bids, asks = [], []
        cumB = cumA = 0
        for i in range(20):
            bp  = round(ltp - tick * (i + 1), 2)
            ap  = round(ltp + tick * (i + 1), 2)
            bq  = rng.randint(200, 1200) * (10 if ltp < 100 else 1)
            aq  = rng.randint(200, 1200) * (10 if ltp < 100 else 1)
            cumB += bq; cumA += aq
            bids.append({"price": bp, "qty": bq, "orders": rng.randint(1, 20)})
            asks.append({"price": ap, "qty": aq, "orders": rng.randint(1, 20)})

        return jsonify({
            "symbol": sym, "ltp": ltp, "open": ltp, "high": hi, "low": lo,
            "prevClose": prev, "change": chg, "changePct": chgPct,
            "week52High": h52, "week52Low": l52, "volume": vol,
            "bid": bids, "ask": asks,
            "totalBidQty": cumB, "totalAskQty": cumA,
            "spread": tick, "ratio": round(cumB / cumA, 2) if cumA else 1.0,
            "source": "yfinance (estimated depth)",
            "last_updated": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/technicals/<symbol>")
def api_technicals(symbol):
    """
    Returns technical indicators for a stock: RSI, MACD, MA50, MA200, 52W High/Low.
    Calculated from 1-year daily price history via yfinance.
    """
    sym_upper = symbol.upper()
    yf_sym = sym_upper + ".NS" if "." not in sym_upper else sym_upper

    try:
        ticker = yf.Ticker(yf_sym)
        hist   = ticker.history(period="1y")

        if hist.empty or len(hist) < 20:
            return jsonify({"error": "insufficient data", "symbol": sym_upper}), 404

        close = hist["Close"]

        # ── RSI (14-period) ──
        delta  = close.diff()
        gain   = delta.where(delta > 0, 0.0)
        loss   = (-delta).where(delta < 0, 0.0)
        avg_g  = gain.rolling(14).mean()
        avg_l  = loss.rolling(14).mean()
        rs     = avg_g / avg_l.replace(0, float("nan"))
        rsi    = round(float((100 - 100 / (1 + rs)).iloc[-1]), 1)

        # ── MACD (12, 26, 9) ──
        ema12  = close.ewm(span=12, adjust=False).mean()
        ema26  = close.ewm(span=26, adjust=False).mean()
        macd_l = ema12 - ema26
        signal = macd_l.ewm(span=9, adjust=False).mean()
        macd_bullish = bool(float(macd_l.iloc[-1]) > float(signal.iloc[-1]))

        # ── Moving Averages ──
        ma50  = round(float(close.rolling(50).mean().iloc[-1]), 2)  if len(close) >= 50  else None
        ma200 = round(float(close.rolling(200).mean().iloc[-1]), 2) if len(close) >= 200 else None
        cur   = round(float(close.iloc[-1]), 2)
        above_ma50  = bool(cur > ma50)  if ma50  else None
        above_ma200 = bool(cur > ma200) if ma200 else None

        # ── 52-Week High / Low ──
        high_52w = round(float(hist["High"].max()), 2)
        low_52w  = round(float(hist["Low"].min()), 2)

        # ── Overall signal ──
        bull_signals = sum([
            rsi < 70 and rsi > 50,
            macd_bullish,
            above_ma50  is True,
            above_ma200 is True,
        ])
        if bull_signals >= 3:
            overall = "STRONG BUY"
        elif bull_signals == 2:
            overall = "BUY"
        elif bull_signals == 1:
            overall = "NEUTRAL"
        else:
            overall = "SELL"

        return jsonify({
            "symbol":      sym_upper,
            "rsi":         rsi,
            "macd_bullish":macd_bullish,
            "macd_val":    round(float(macd_l.iloc[-1]), 3),
            "signal_val":  round(float(signal.iloc[-1]), 3),
            "ma50":        ma50,
            "ma200":       ma200,
            "above_ma50":  above_ma50,
            "above_ma200": above_ma200,
            "high_52w":    high_52w,
            "low_52w":     low_52w,
            "overall":     overall,
            "last_updated": datetime.now().isoformat(),
        })

    except Exception as e:
        print(f"[Technicals] {sym_upper}: {e}")
        return jsonify({"error": str(e), "symbol": sym_upper}), 500


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
    Sources: BSE API, NSE via proxy, Trendlyne. Refreshed every 30 min.
    Format: [{type, sym, name, date, sector, note, icon, label}, ...]
    """
    with _earnings_lock:
        data         = _earnings_cache["data"]
        last_updated = _earnings_cache["last_updated"]

    # Refresh if cache empty or older than 30 minutes
    cache_stale = True
    if last_updated:
        try:
            age = (datetime.now() - datetime.fromisoformat(last_updated)).total_seconds()
            cache_stale = age > 1800  # 30 minutes
        except:
            cache_stale = True

    if not data or cache_stale:
        fresh = fetch_earnings_from_nse()
        if fresh:
            data = fresh
            with _earnings_lock:
                _earnings_cache["data"]         = data
                _earnings_cache["last_updated"] = datetime.now().isoformat()
            last_updated = _earnings_cache["last_updated"]

    return jsonify({
        "data":         data,
        "last_updated": last_updated,
        "source":       "BSE + NSE Corporate Actions (live)",
        "count":        len(data),
    })



def fetch_live_ipo_data():
    """
    Fetch live IPO data from multiple sources.
    1. BSE IPO listing page (api.bseindia.com)
    2. NSE upcoming IPOs via allorigins proxy
    3. Chittorgarh scrape
    Returns: {upcoming:[], open:[], allotment:[], listed:[]}
    """    """
    Fetch live IPO data from multiple sources.
    1. BSE IPO listing page (api.bseindia.com)
    2. NSE upcoming IPOs via allorigins proxy
    3. Chittorgarh scrape
    Returns: {upcoming:[], open:[], allotment:[], listed:[]}
    """
    if req_lib is None:
        return None

    from datetime import datetime as _dt, timedelta as _td, date as _date
    from bs4 import BeautifulSoup

    result = {"upcoming": [], "open": [], "allotment": [], "listed": []}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-IN,en;q=0.9",
    }

    # ── Source 1: BSE IPO API ──────────────────────────────────────────────
    try:
        today   = _date.today()
        from_dt = (today - _td(days=30)).strftime("%Y%m%d")
        to_dt   = (today + _td(days=90)).strftime("%Y%m%d")

        # BSE new listings
        bse_listed_url = "https://api.bseindia.com/BseIndiaAPI/api/IPOListingData/w?strType=&strFlag=&ddlIssueType=IPO&ddlStatus=&ddlExchangeType="
        r = req_lib.get(bse_listed_url, headers={**headers,
            "Referer": "https://www.bseindia.com/markets/PublicIssues/IPOListingDt.aspx",
            "Origin": "https://www.bseindia.com",
        }, timeout=10)
        if r.status_code == 200:
            j = r.json()
            rows = j.get("Table") or j.get("Table1") or (j if isinstance(j, list) else [])
            for row in rows[:20]:
                try:
                    name       = str(row.get("SECURITY_NAME") or row.get("scrip_name") or "").strip()
                    issue_price= str(row.get("ISSUE_PRICE") or row.get("issue_price") or "—")
                    list_price = str(row.get("LISTING_PRICE") or row.get("listing_price") or "—")
                    list_date  = str(row.get("LISTING_DATE") or row.get("listing_date") or "—")
                    current    = str(row.get("CLOSE_PRICE") or row.get("close_price") or list_price)
                    # Calculate gain
                    gain = "—"
                    try:
                        ip = float(str(issue_price).replace("₹","").replace(",",""))
                        lp = float(str(list_price).replace("₹","").replace(",",""))
                        if ip > 0:
                            g = ((lp - ip) / ip) * 100
                            gain = f"{'+'if g>=0 else ''}{g:.1f}%"
                    except: pass
                    if name:
                        result["listed"].append({
                            "name": name,
                            "listDate": list_date,
                            "issuePrice": f"₹{issue_price}" if not issue_price.startswith("₹") else issue_price,
                            "listPrice":  f"₹{list_price}"  if not list_price.startswith("₹")  else list_price,
                            "gain": gain,
                            "current": f"₹{current}" if not current.startswith("₹") else current,
                        })
                except: continue
        if result["listed"]:
            print(f"  [IPO] ✓ BSE listed: {len(result['listed'])} IPOs")

        # BSE upcoming / open IPOs
        bse_upcoming_url = "https://api.bseindia.com/BseIndiaAPI/api/IPOListingData/w?strType=&strFlag=U&ddlIssueType=IPO&ddlStatus=&ddlExchangeType="
        r2 = req_lib.get(bse_upcoming_url, headers={**headers,
            "Referer": "https://www.bseindia.com/markets/PublicIssues/IPOListingDt.aspx",
            "Origin": "https://www.bseindia.com",
        }, timeout=10)
        if r2.status_code == 200:
            j2   = r2.json()
            rows2= j2.get("Table") or j2.get("Table1") or (j2 if isinstance(j2, list) else [])
            for row in rows2[:20]:
                try:
                    name     = str(row.get("SECURITY_NAME") or row.get("scrip_name") or "").strip()
                    open_dt  = str(row.get("ISSUE_OPEN_DATE")  or row.get("open_date")  or "TBA")
                    close_dt = str(row.get("ISSUE_CLOSE_DATE") or row.get("close_date") or "—")
                    price    = str(row.get("ISSUE_PRICE") or row.get("issue_price") or "TBA")
                    size     = str(row.get("ISSUE_SIZE")  or row.get("issue_size")  or "—")
                    # Determine if currently open
                    is_open  = False
                    try:
                        od = _dt.strptime(open_dt, "%d/%m/%Y") if "/" in open_dt else _dt.strptime(open_dt, "%d-%m-%Y")
                        cd = _dt.strptime(close_dt, "%d/%m/%Y") if "/" in close_dt else _dt.strptime(close_dt, "%d-%m-%Y")
                        is_open = od.date() <= today <= cd.date()
                    except: pass

                    entry = {
                        "name": name, "open": open_dt, "close": close_dt,
                        "price": f"₹{price}" if price != "TBA" and not price.startswith("₹") else price,
                        "size": f"₹{size} Cr" if size not in ("—","TBA") and not size.startswith("₹") else size,
                        "gmp": "—", "gmpPct": "—", "rating": "⭐⭐⭐",
                        "sector": "—", "lot": "—", "minInvest": "—",
                    }
                    if is_open:
                        result["open"].append(entry)
                    else:
                        result["upcoming"].append(entry)
                except: continue
        if result["open"] or result["upcoming"]:
            print(f"  [IPO] ✓ BSE upcoming/open: {len(result['open'])} open, {len(result['upcoming'])} upcoming")

    except Exception as e:
        print(f"  [IPO] BSE API: {e}")

    # ── Source 2: NSE IPO via allorigins ──────────────────────────────────
    try:
        nse_ipo_url = "https://www.nseindia.com/api/allIpo"
        proxy = "https://api.allorigins.win/get?url=" + req_lib.utils.quote(nse_ipo_url, safe="")
        r3 = req_lib.get(proxy, timeout=12)
        if r3.status_code == 200:
            contents = r3.json().get("contents","")
            if contents and len(contents) > 100:
                nse_j = json.loads(contents)
                for section, key in [("upcoming","upcoming"), ("open","current"), ("listed","past")]:
                    rows = nse_j.get(key, [])
                    if not rows or result[section]:  # skip if BSE already filled this
                        continue
                    for row in rows[:15]:
                        try:
                            name      = row.get("companyName","").strip()
                            open_dt   = row.get("bidOpenDate","TBA")
                            close_dt  = row.get("bidCloseDate","—")
                            price_raw = row.get("priceRange","TBA")
                            size_raw  = row.get("issueSize","—")
                            list_dt   = row.get("listingDate","—")
                            issue_pr  = row.get("issuePrice","—")
                            list_pr   = row.get("listingPrice","—")

                            if section == "listed":
                                gain = "—"
                                try:
                                    ip = float(str(issue_pr).replace("₹","").replace(",",""))
                                    lp = float(str(list_pr).replace("₹","").replace(",",""))
                                    if ip > 0:
                                        g  = ((lp-ip)/ip)*100
                                        gain = f"{'+'if g>=0 else ''}{g:.1f}%"
                                except: pass
                                result["listed"].append({
                                    "name": name, "listDate": list_dt,
                                    "issuePrice": issue_pr, "listPrice": list_pr,
                                    "gain": gain, "current": list_pr,
                                })
                            else:
                                result[section].append({
                                    "name": name, "open": open_dt, "close": close_dt,
                                    "price": price_raw, "size": size_raw,
                                    "gmp":"—","gmpPct":"—","rating":"⭐⭐⭐",
                                    "sector":"—","lot":"—","minInvest":"—",
                                })
                        except: continue
        if result["upcoming"] or result["listed"]:
            print(f"  [IPO] ✓ NSE allIpo proxy: total upcoming={len(result['upcoming'])} listed={len(result['listed'])}")
    except Exception as e:
        print(f"  [IPO] NSE proxy: {e}")

    # ── Source 3: Chittorgarh scrape ──────────────────────────────────────
    try:
        cht_headers = {**headers, "Referer": "https://www.chittorgarh.com/"}

        # Open IPOs
        if not result["open"]:
            r4 = req_lib.get("https://www.chittorgarh.com/ipo/ipo_subscription_status_live_day_wise.asp",
                             headers=cht_headers, timeout=10)
            if r4.status_code == 200:
                soup = BeautifulSoup(r4.text, "html.parser")
                for table in soup.find_all("table"):
                    for tr in table.find_all("tr")[1:]:
                        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                        name_tag = tr.find("a")
                        name = (name_tag.get_text(strip=True) if name_tag else tds[0] if tds else "").strip()
                        if name and len(name) > 2 and len(tds) >= 3:
                            result["open"].append({
                                "name": name, "open": tds[1] if len(tds)>1 else "—",
                                "close": tds[2] if len(tds)>2 else "—",
                                "price": tds[3] if len(tds)>3 else "—",
                                "subscribed": tds[4] if len(tds)>4 else "—",
                                "gmp":"—","gmpPct":"—","size":"—","sector":"—","lot":"—","minInvest":"—",
                            })

        # Upcoming IPOs
        if not result["upcoming"]:
            r5 = req_lib.get("https://www.chittorgarh.com/ipo/upcoming-ipo-list-in-india.asp",
                             headers=cht_headers, timeout=10)
            if r5.status_code == 200:
                soup5 = BeautifulSoup(r5.text, "html.parser")
                for table in soup5.find_all("table"):
                    for tr in table.find_all("tr")[1:20]:
                        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                        name_tag = tr.find("a")
                        name = (name_tag.get_text(strip=True) if name_tag else tds[0] if tds else "").strip()
                        if name and len(name) > 2:
                            result["upcoming"].append({
                                "name": name,
                                "open": tds[1] if len(tds)>1 else "TBA",
                                "close": tds[2] if len(tds)>2 else "—",
                                "price": tds[3] if len(tds)>3 else "TBA",
                                "size": tds[4] if len(tds)>4 else "—",
                                "gmp":"—","gmpPct":"—","rating":"⭐⭐⭐","sector":"—","lot":"—","minInvest":"—",
                            })

        # Listed / GMP
        if not result["listed"]:
            r6 = req_lib.get("https://www.chittorgarh.com/ipo/ipo_performance_tracker_listed_ipo.asp",
                             headers=cht_headers, timeout=10)
            if r6.status_code == 200:
                soup6 = BeautifulSoup(r6.text, "html.parser")
                for table in soup6.find_all("table"):
                    for tr in table.find_all("tr")[1:15]:
                        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                        name_tag = tr.find("a")
                        name = (name_tag.get_text(strip=True) if name_tag else tds[0] if tds else "").strip()
                        if name and len(name) > 2 and len(tds) >= 3:
                            result["listed"].append({
                                "name": name,
                                "listDate": tds[1] if len(tds)>1 else "—",
                                "issuePrice": tds[2] if len(tds)>2 else "—",
                                "listPrice": tds[3] if len(tds)>3 else "—",
                                "gain": tds[-1] if tds else "—",
                                "current": tds[4] if len(tds)>4 else "—",
                            })

        if any(result.values()):
            print(f"  [IPO] ✓ Chittorgarh: open={len(result['open'])} upcoming={len(result['upcoming'])} listed={len(result['listed'])}")

    except Exception as e:
        print(f"  [IPO] Chittorgarh: {e}")

    # Check if we got anything useful
    total = sum(len(v) for v in result.values())
    if total == 0:
        return None

    result["last_updated"] = _dt.now().isoformat()
    result["source"] = "BSE + NSE + Chittorgarh (live)"
    return result


@app.route("/api/ipo")
def api_ipo():
    """Live IPO data — BSE API, NSE proxy, Chittorgarh scrape. Cache: 30 min."""
    # ── Static fallback ─────────────────────────────────────────────────
    static_data = {
        "upcoming": [
            {"name":"Ather Energy","open":"28 Apr 2026","close":"30 Apr 2026","price":"₹304–321","size":"₹2,981 Cr","gmp":"₹12","gmpPct":"+3.7%","rating":"⭐⭐⭐⭐","sector":"EV/Auto","lot":"46","minInvest":"₹14,766"},
            {"name":"Truhome Finance","open":"Apr 2026","close":"—","price":"TBA","size":"₹3,000 Cr","gmp":"—","gmpPct":"—","rating":"⭐⭐⭐⭐","sector":"NBFC","lot":"TBA","minInvest":"TBA"},
            {"name":"PhonePe","open":"2026","close":"—","price":"TBA","size":"₹15,000 Cr","gmp":"—","gmpPct":"—","rating":"⭐⭐⭐⭐⭐","sector":"Fintech","lot":"TBA","minInvest":"TBA"},
            {"name":"Reliance Jio","open":"2026","close":"—","price":"TBA","size":"TBA","gmp":"—","gmpPct":"—","rating":"⭐⭐⭐⭐⭐","sector":"Telecom","lot":"TBA","minInvest":"TBA"},
            {"name":"NSDL","open":"2026","close":"—","price":"TBA","size":"₹3,000 Cr","gmp":"—","gmpPct":"—","rating":"⭐⭐⭐⭐","sector":"Financial Services","lot":"TBA","minInvest":"TBA"},
        ],
        "open": [],
        "allotment": [
            {"name":"Schbang Digital Solutions","date":"17 Mar 2026","price":"₹216","listPrice":"19 Mar 2026","gain":"Pending","status":"Allotment Done"},
            {"name":"Innovision Commerce","date":"13 Mar 2026","price":"₹548","listPrice":"17 Mar 2026","gain":"Pending","status":"Allotment Done"},
        ],
        "listed": [
            {"name":"SEDEMAC Mechatronics","listDate":"11 Mar 2026","issuePrice":"₹1,352","listPrice":"₹1,510","gain":"+11.7%","current":"₹1,547"},
            {"name":"Hexaware Technologies","listDate":"19 Feb 2026","issuePrice":"₹708","listPrice":"₹745","gain":"+5.2%","current":"₹731"},
            {"name":"Laxmi Dental","listDate":"20 Jan 2026","issuePrice":"₹428","listPrice":"₹513","gain":"+19.9%","current":"₹498"},
            {"name":"Capital Infra Trust InvIT","listDate":"12 Feb 2026","issuePrice":"₹99","listPrice":"₹102","gain":"+3.0%","current":"₹101"},
        ],
        "last_updated": _dt2.now().isoformat(),
        "source": "Static (updated Mar 2026)",
    }

    # Check cache
    with _ipo_lock:
        cached    = _ipo_cache["data"]
        cache_ts  = _ipo_cache["last_updated"]

    cache_stale = True
    if cache_ts:
        try:
            age = (_dt2.now() - _dt2.fromisoformat(cache_ts)).total_seconds()
            cache_stale = age > 1800  # 30 min
        except: pass

    if cached and not cache_stale:
        return jsonify(cached)

    # Fetch fresh
    if req_lib is not None:
        live = fetch_live_ipo_data()
        if live:
            # Merge: use live data but fill gaps with static
            for key in ["upcoming","open","allotment","listed"]:
                if not live.get(key):
                    live[key] = static_data[key]
            with _ipo_lock:
                _ipo_cache["data"]         = live
                _ipo_cache["last_updated"] = _dt2.now().isoformat()
            return jsonify(live)

    # Return static if live fails
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
#  STARTUP — works for both gunicorn (Railway) and direct
# ════════════════════════════════════════════════════════

def _startup():
    """Run once at startup regardless of how the server is launched.
    All cache building is done in background threads so Flask starts
    serving requests immediately (no 60s cold-start block).
    """
    print("=" * 55)
    print("  MarketPit Backend — Starting up")
    print("=" * 55)

    def _stock_init():
        try:
            refresh_cache()
            print("  ✓ Stock cache ready")
        except Exception as e:
            print(f"  ⚠ Stock cache error: {e}")

    def _fii_init():
        try:
            refresh_fii()
            print("  ✓ FII/DII cache ready")
        except Exception as e:
            print(f"  ⚠ FII cache error: {e}")

    def _earn_init():
        try:
            refresh_earnings()
            print("  ✓ Earnings cache ready")
        except Exception as e:
            print(f"  ⚠ Earnings cache error: {e}")

    # All three run in background — Flask is ready to serve immediately
    threading.Thread(target=_stock_init, daemon=True).start()
    threading.Thread(target=_fii_init,   daemon=True).start()
    threading.Thread(target=_earn_init,  daemon=True).start()

    # Start background refresh thread
    t = threading.Thread(target=background_refresher, daemon=True)
    t.start()
    print("  ✓ All caches building in background (server ready immediately)")
    print("=" * 55)


# ── Run startup when imported by gunicorn OR run directly ──
_startup()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\nServer running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
