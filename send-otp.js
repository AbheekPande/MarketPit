// api/send-otp.js — Vercel Serverless Function
// Proxies POST /api/send-otp to Railway backend
const https = require('https');

const RAILWAY = 'https://web-production-78fc1.up.railway.app';

function postToRailway(url, body) {
  return new Promise((resolve, reject) => {
    const parsed  = new URL(url);
    const data    = JSON.stringify(body);
    const options = {
      hostname: parsed.hostname,
      path:     parsed.pathname,
      port:     443,
      method:   'POST',
      headers:  {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(data),
        'User-Agent':     'Vercel-Proxy/1.0',
      },
      timeout: 28000,
    };
    const req = https.request(options, (res) => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
    });
    req.on('error',   reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(data);
    req.end();
  });
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin',  '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST')   return res.status(405).json({ ok: false, message: 'Method not allowed' });

  try {
    const { status, body } = await postToRailway(`${RAILWAY}/api/send-otp`, req.body || {});
    const json = JSON.parse(body);
    return res.status(status).json(json);
  } catch (e) {
    return res.status(502).json({ ok: false, message: 'Railway unavailable: ' + e.message });
  }
};
