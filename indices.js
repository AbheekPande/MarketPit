// /api/indices.js — Vercel Serverless Function
// Returns Nifty 50, BankNifty, Sensex live prices
// Uses multiple Yahoo Finance endpoints with fallbacks
const https = require('https');
const zlib  = require('zlib');

function fetch_url(url) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const opts = {
      hostname: parsed.hostname,
      path: parsed.pathname + parsed.search,
      port: 443,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'no-cache',
      },
      timeout: 12000,
    };
    const req = https.get(opts, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch_url(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks);
        if (res.headers['content-encoding'] === 'gzip') {
          zlib.gunzip(buf, (err, dec) => {
            if (err) reject(err);
            else resolve({ status: res.statusCode, body: dec.toString() });
          });
        } else {
          resolve({ status: res.statusCode, body: buf.toString() });
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function fmtQ(q) {
  if (!q || !q.regularMarketPrice) return null;
  const price = q.regularMarketPrice;
  const chg   = q.regularMarketChangePercent || 0;
  return {
    sym:   q.symbol,
    name:  q.shortName || q.symbol,
    price: price,
    chg:   (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%',
    up:    chg >= 0,
  };
}

// Fetch individual index using chart API (more reliable)
async function fetchIndexChart(sym, name) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?interval=1d&range=2d`;
    const { status, body } = await fetch_url(url);
    if (status === 200) {
      const json = JSON.parse(body);
      const meta = json?.chart?.result?.[0]?.meta;
      if (meta?.regularMarketPrice) {
        const price = meta.regularMarketPrice;
        const prev  = meta.previousClose || meta.chartPreviousClose || price;
        const chg   = prev ? ((price - prev) / prev * 100) : 0;
        return {
          sym, name, price,
          chg: (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%',
          up:  chg >= 0,
        };
      }
    }
  } catch(e) {}
  return null;
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=20');

  // Try v7 batch first (fastest)
  // Yahoo Finance symbols: ^NSEI = Nifty50, ^NSEBANK = BankNifty, ^BSESN = Sensex
  const SYMS = '^NSEI,^NSEBANK,^BSESN';
  const urls = [
    `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(SYMS)}&fields=regularMarketPrice,regularMarketChangePercent,shortName`,
    `https://query2.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(SYMS)}&fields=regularMarketPrice,regularMarketChangePercent,shortName`,
  ];

  for (const url of urls) {
    try {
      const { status, body } = await fetch_url(url);
      if (status === 200 && body) {
        const json    = JSON.parse(body);
        const results = json?.quoteResponse?.result || [];
        if (results.length > 0) {
          const nifty     = fmtQ(results.find(q => q.symbol === '^NSEI'));
          const banknifty = fmtQ(results.find(q => q.symbol === '^NSEBANK'));
          const sensex    = fmtQ(results.find(q => q.symbol === '^BSESN'));

          if (nifty || banknifty) {
            return res.status(200).json({
              nifty:     nifty     || null,
              banknifty: banknifty || null,
              sensex:    sensex    || null,
              ts: new Date().toISOString(),
              source: 'yahoo-v7',
            });
          }
        }
      }
    } catch(e) { continue; }
  }

  // Fallback: fetch each index individually via chart API
  const [nifty, banknifty, sensex] = await Promise.all([
    fetchIndexChart('%5ENSEI',    'Nifty 50'),
    fetchIndexChart('%5ENSEBANK', 'Bank Nifty'),
    fetchIndexChart('%5EBSESN',   'Sensex'),
  ]);

  if (nifty || banknifty || sensex) {
    return res.status(200).json({
      nifty, banknifty, sensex,
      ts: new Date().toISOString(),
      source: 'yahoo-chart',
    });
  }

  // Last resort: try Nifty and BankNifty with alternate symbols
  const [n2, b2] = await Promise.all([
    fetchIndexChart('NIFTY50.NS',  'Nifty 50'),
    fetchIndexChart('NIFTYBANK.NS','Bank Nifty'),
  ]);

  return res.status(200).json({
    nifty:     n2 || null,
    banknifty: b2 || null,
    sensex:    null,
    ts: new Date().toISOString(),
    source: 'yahoo-ns',
  });
};
