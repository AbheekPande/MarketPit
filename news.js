// /api/news.js — Vercel Serverless Function
// Fetches Google News RSS server-side and returns parsed JSON
// No CORS issues, no proxy needed, auto-updates on every call

const https = require('https');
const zlib  = require('zlib');

const RSS_URLS = {
  markets:     'https://news.google.com/rss/search?q=indian+stock+market+nifty+sensex&hl=en-IN&gl=IN&ceid=IN:en',
  stocks:      'https://news.google.com/rss/search?q=NSE+BSE+india+stocks+today&hl=en-IN&gl=IN&ceid=IN:en',
  economy:     'https://news.google.com/rss/search?q=india+economy+RBI+inflation+2026&hl=en-IN&gl=IN&ceid=IN:en',
  crypto:      'https://news.google.com/rss/search?q=bitcoin+crypto+cryptocurrency+today&hl=en-IN&gl=IN&ceid=IN:en',
  commodities: 'https://news.google.com/rss/search?q=gold+price+crude+oil+india+today&hl=en-IN&gl=IN&ceid=IN:en',
};

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const opts = {
      hostname: parsed.hostname,
      path: parsed.pathname + parsed.search,
      port: 443,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      timeout: 10000,
    };
    const req = https.get(opts, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchUrl(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks);
        if (res.headers['content-encoding'] === 'gzip') {
          zlib.gunzip(buf, (err, dec) => {
            if (err) reject(err);
            else resolve({ status: res.statusCode, body: dec.toString('utf8') });
          });
        } else {
          resolve({ status: res.statusCode, body: buf.toString('utf8') });
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

// Simple XML parser — extracts <item> blocks without a library
function parseRSS(xml) {
  const items = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;
  while ((match = itemRegex.exec(xml)) !== null) {
    const block = match[1];
    const get = (tag) => {
      const m = block.match(new RegExp(`<${tag}[^>]*>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?<\\/${tag}>`, 'i'));
      return m ? m[1].trim().replace(/<[^>]+>/g, '') : '';
    };
    const title   = get('title');
    const link    = get('link') || block.match(/<link\/>(.*?)<\//)?.[1] || '';
    const pubDate = get('pubDate');
    const source  = get('source');
    if (title && title.length > 8) {
      items.push({ title, link: link.trim(), date: pubDate, source: source || 'Google News' });
    }
  }
  return items;
}

// Format time ago
function timeAgo(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)  return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24)  return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  } catch(e) { return ''; }
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=120, stale-while-revalidate=60'); // 2min cache

  const cat = (req.query.cat || 'markets').replace(/[^a-z]/g, '');
  const rssUrl = RSS_URLS[cat] || RSS_URLS.markets;

  try {
    const { status, body } = await fetchUrl(rssUrl);
    if (status !== 200 || !body.includes('<item>')) {
      return res.status(502).json({ error: 'RSS fetch failed', status });
    }
    const items = parseRSS(body).slice(0, 16).map(item => ({
      ...item,
      ago: timeAgo(item.date),
    }));
    return res.status(200).json({ items, cat, ts: new Date().toISOString() });
  } catch(e) {
    return res.status(500).json({ error: e.message });
  }
};
