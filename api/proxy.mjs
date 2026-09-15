const safePath = value => {
  const path = Array.isArray(value) ? value.join('/') : String(value || '');
  if (!path || path.includes('..') || !/^[a-zA-Z0-9/_-]+$/.test(path)) throw new Error('Invalid API path.');
  return path.replace(/^\/+/, '');
};

export default async function handler(req, res) {
  try {
    const base = new URL(process.env.BACKEND_URL || '');
    if (!['https:', 'http:'].includes(base.protocol) || base.username || base.password) throw new Error('BACKEND_URL is not configured.');
    const path = safePath(req.query?.path);
    const headers = {'Content-Type': 'application/json'};
    if (req.headers['x-workspace-id']) headers['X-Workspace-ID'] = req.headers['x-workspace-id'];
    const password = process.env.BACKEND_ACCESS_PASSWORD || '';
    if (password) headers.Authorization = 'Basic ' + Buffer.from(`reviewer:${password}`).toString('base64');
    const body = ['GET', 'HEAD'].includes(req.method) ? undefined :
      (typeof req.body === 'string' ? req.body : JSON.stringify(req.body ?? {}));
    const upstream = await fetch(`${base.href.replace(/\/$/, '')}/api/${path}`, {method:req.method, headers, body, signal:AbortSignal.timeout(285000)});
    res.statusCode = upstream.status;
    res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json');
    res.setHeader('Cache-Control', 'no-store');
    res.end(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    res.statusCode = error instanceof TypeError ? 502 : 503;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({error:{code:'backend_unavailable', message:'The hosted backend is not connected. Configure BACKEND_URL and BACKEND_ACCESS_PASSWORD in Vercel.'}}));
  }
}
