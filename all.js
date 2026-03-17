// /api/all.js — Vercel Serverless Function (CommonJS)
// Proxies Railway /api/all — wakes Railway if sleeping, returns all stock data
const https = require('https');

function httpsGet(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      timeout: 30000,
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

const RAILWAY = 'https://web-production-78fc1.up.railway.app/api';

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=25, stale-while-revalidate=30');

  const path = req.query.path || 'all';
  const allowed = ['all', 'stocks', 'indices', 'fii', 'earnings', 'status'];
  if (!allowed.includes(path)) return res.status(400).json({ error: 'invalid path' });

  try {
    const body = await httpsGet(RAILWAY + '/' + path);
    const json = JSON.parse(body);
    return res.status(200).json(json);
  } catch (e) {
    return res.status(502).json({ error: 'Railway unavailable: ' + e.message });
  }
};
