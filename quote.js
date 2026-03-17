// /api/quote.js  — Vercel Serverless Function (CommonJS)
// Usage: /api/quote?symbols=RELIANCE.NS,TCS.NS,HDFCBANK.NS
const https = require('https');

function httpsGet(url, redirects) {
  redirects = redirects || 0;
  if (redirects > 3) return Promise.reject(new Error('too many redirects'));
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      timeout: 9000,
    }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return resolve(httpsGet(res.headers.location, redirects + 1));
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

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=20, stale-while-revalidate=30');

  const symbols = req.query.symbols;
  if (!symbols) return res.status(400).json({ error: 'symbols param required' });

  const urls = [
    'https://query1.finance.yahoo.com/v7/finance/quote?symbols=' + encodeURIComponent(symbols) + '&fields=regularMarketPrice,regularMarketChangePercent,regularMarketPreviousClose,shortName,currency',
    'https://query2.finance.yahoo.com/v7/finance/quote?symbols=' + encodeURIComponent(symbols) + '&fields=regularMarketPrice,regularMarketChangePercent,regularMarketPreviousClose,shortName,currency',
  ];

  for (const url of urls) {
    try {
      const body = await httpsGet(url);
      const json = JSON.parse(body);
      if (json && json.quoteResponse) return res.status(200).json(json);
    } catch (e) { /* try next */ }
  }

  return res.status(502).json({ error: 'Yahoo Finance unavailable' });
};
