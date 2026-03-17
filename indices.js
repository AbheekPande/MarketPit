// Vercel Serverless Function — /api/indices
// Returns Nifty 50, Bank Nifty, Sensex spot prices from Yahoo Finance

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=20');

  const INDICES = '%5ENSEI,%5ENSEBANK,%5EBSESN'; // ^NSEI, ^NSEBANK, ^BSESN
  const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${INDICES}&fields=regularMarketPrice,regularMarketChangePercent,regularMarketPreviousClose,shortName`;

  try {
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' },
      signal: AbortSignal.timeout(8000),
    });
    const data = await r.json();
    const results = data?.quoteResponse?.result || [];

    const fmt = (q) => ({
      sym:   q.symbol,
      name:  q.shortName || q.symbol,
      price: q.regularMarketPrice,
      chg:   (q.regularMarketChangePercent >= 0 ? '+' : '') + (q.regularMarketChangePercent || 0).toFixed(2) + '%',
      up:    (q.regularMarketChangePercent || 0) >= 0,
    });

    return res.status(200).json({
      nifty:    fmt(results.find(q => q.symbol === '^NSEI')    || {}),
      banknifty: fmt(results.find(q => q.symbol === '^NSEBANK') || {}),
      sensex:   fmt(results.find(q => q.symbol === '^BSESN')   || {}),
      ts:       new Date().toISOString(),
    });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
