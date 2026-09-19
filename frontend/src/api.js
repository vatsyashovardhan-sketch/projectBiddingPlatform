// Explicit VITE_API_URL wins. Otherwise: local dev talks to the local
// backend, while any deployed preview/production page talks to Render.
const PROD_API_URL = 'https://projectbiddingplatform.onrender.com';
const onLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const BASE = import.meta.env.VITE_API_URL || (onLocalhost ? 'http://localhost:8000' : PROD_API_URL);

function tokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

async function refreshAccess() {
  const { refresh } = tokens();
  if (!refresh) return null;
  const r = await fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!r.ok) return null;
  const data = await r.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data.access_token;
}

export async function api(path, opts = {}, retry = true) {
  const { access } = tokens();
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...opts,
      headers: {
        ...(opts.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(opts.headers || {}),
        ...(access ? { Authorization: `Bearer ${access}` } : {}),
      },
    });
  } catch (e) {
    // Network-level failure: backend down, wrong VITE_API_URL, or a
    // browser CORS block (all surface as TypeError: Failed to fetch).
    throw new Error(
      `Cannot reach the backend at ${BASE}. Is it running, is VITE_API_URL correct, ` +
      `and is this site's origin allowed by the backend's FRONTEND_URL (CORS)?`
    );
  }
  if (res.status === 401 && retry) {
    const next = await refreshAccess();
    if (next) return api(path, opts, false);
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      msg = j.detail || JSON.stringify(j);
    } catch {}
    throw new Error(msg);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

export const API_BASE = BASE;
