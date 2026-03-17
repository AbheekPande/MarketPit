// /api/all.js — Vercel Serverless Function
// Proxies Railway /api/all server-side — bypasses CORS and cold-start issues
const https = require('https');
const zlib  = require('zlib');

const RAILWAY = 'https://web-production-78fc1.up.railway.app';

function fetch_url(url) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const opts = {
      hostname: parsed.hostname,
      path: parsed.pathname + parsed.search,
      port: 443,
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
      },
      timeout: 28000,
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

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=25, stale-while-revalidate=30');

  const path = (req.query.path || 'all').replace(/[^a-z]/g, '');
  const allowed = ['all', 'stocks', 'indices', 'fii', 'earnings', 'status'];
  if (!allowed.includes(path)) return res.status(400).json({ error: 'invalid path' });

  try {
    const { status, body } = await fetch_url(`${RAILWAY}/api/${path}`);
    if (status === 200 && body) {
      const json = JSON.parse(body);
      return res.status(200).json(json);
    }
    return res.status(status).json({ error: `Railway returned ${status}` });
  } catch(e) {
    return res.status(502).json({ error: 'Railway unavailable: ' + e.message });
  }
};
