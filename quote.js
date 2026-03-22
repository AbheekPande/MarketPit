// /api/quote.js — Vercel Serverless Function
// Fetches Yahoo Finance data server-side using multiple methods
const https = require('https');
const http  = require('http');

function fetch_url(url, headers) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const opts = {
      headers: headers || {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
      },
      timeout: 12000,
    };
    const parsed = new URL(url);
    opts.hostname = parsed.hostname;
    opts.path = parsed.pathname + parsed.search;
    opts.port = parsed.port || (url.startsWith('https') ? 443 : 80);

    const req = lib.get(opts, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch_url(res.headers.location, headers).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const body = Buffer.concat(chunks);
        // Handle gzip
        if (res.headers['content-encoding'] === 'gzip') {
          const zlib = require('zlib');
          zlib.gunzip(body, (err, decoded) => {
            if (err) reject(err);
            else resolve({ status: res.statusCode, body: decoded.toString() });
          });
        } else {
          resolve({ status: res.statusCode, body: body.toString() });
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');

  const symbols = (req.query.symbols || '').trim();
  if (!symbols) return res.status(400).json({ error: 'symbols required' });

  // Try Yahoo Finance v7 quote API — most reliable
  const endpoints = [
    `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(symbols)}&fields=regularMarketPrice,regularMarketChangePercent,regularMarketPreviousClose,shortName,currency`,
    `https://query2.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(symbols)}&fields=regularMarketPrice,regularMarketChangePercent,regularMarketPreviousClose,shortName,currency`,
    // v8 chart API as fallback for individual symbols
  ];

  for (const url of endpoints) {
    try {
      const { status, body } = await fetch_url(url);
      if (status === 200 && body) {
        const json = JSON.parse(body);
        if (json && json.quoteResponse && json.quoteResponse.result && json.quoteResponse.result.length > 0) {
          return res.status(200).json(json);
        }
      }
    } catch (e) {
      continue;
    }
  }

  // Last resort: try v8 chart for first symbol only
  const firstSym = symbols.split(',')[0].trim();
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(firstSym)}?interval=1d&range=5d`;
    const { status, body } = await fetch_url(url);
    if (status === 200) {
      const json = JSON.parse(body);
      const meta = json?.chart?.result?.[0]?.meta;
      if (meta?.regularMarketPrice) {
        const price = meta.regularMarketPrice;
        const prev = meta.previousClose || meta.chartPreviousClose || price;
        const chg = prev ? ((price - prev) / prev * 100) : 0;
        // Return in v7 format so frontend can parse it
        return res.status(200).json({
          quoteResponse: {
            result: [{
              symbol: firstSym,
              regularMarketPrice: price,
              regularMarketChangePercent: chg,
              regularMarketPreviousClose: prev,
              shortName: firstSym,
            }],
            error: null,
          }
        });
      }
    }
  } catch(e) {}

  return res.status(502).json({ error: 'All Yahoo Finance endpoints failed', quoteResponse: { result: [], error: 'upstream' } });
};
