// /api/indices.js — Vercel Serverless Function (CommonJS)
// Returns Nifty 50, Bank Nifty, Sensex live prices from Yahoo Finance
const https = require('https');

function httpsGet(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
      },
      timeout: 9000,
    }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return resolve(httpsGet(res.headers.location));
      }
      if (res.statusCode !== 200) return reject(new Error('HTTP ' + res.statusCode));
      let data = '';
      res.on('data', c => { data += c; });
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function fmt(q) {
  if (!q || !q.regularMarketPrice) return null;
  const chg = q.regularMarketChangePercent || 0;
  return {
    sym:   q.symbol,
    name:  q.shortName || q.symbol,
    price: q.regularMarketPrice,
    chg:   (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%',
    up:    chg >= 0,
  };
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=20');

  const SYMS = '%5ENSEI,%5ENSEBANK,%5EBSESN'; // ^NSEI, ^NSEBANK, ^BSESN
  const urls = [
    'https://query1.finance.yahoo.com/v7/finance/quote?symbols=' + SYMS + '&fields=regularMarketPrice,regularMarketChangePercent,shortName',
    'https://query2.finance.yahoo.com/v7/finance/quote?symbols=' + SYMS + '&fields=regularMarketPrice,regularMarketChangePercent,shortName',
  ];

  for (const url of urls) {
    try {
      const body = await httpsGet(url);
      const json = JSON.parse(body);
      const results = (json && json.quoteResponse && json.quoteResponse.result) || [];
      if (!results.length) continue;
      return res.status(200).json({
        nifty:     fmt(results.find(q => q.symbol === '^NSEI'))    || null,
        banknifty: fmt(results.find(q => q.symbol === '^NSEBANK')) || null,
        sensex:    fmt(results.find(q => q.symbol === '^BSESN'))   || null,
        ts: new Date().toISOString(),
      });
    } catch (e) { /* try next */ }
  }

  return res.status(502).json({ error: 'Yahoo Finance unavailable' });
};
