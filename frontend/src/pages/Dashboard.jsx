import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

export function Dashboard() {
  const { user } = useAuth();
  const [listings, setListings] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [sales, setSales] = useState([]);
  const [bids, setBids] = useState([]);
  const [incoming, setIncoming] = useState([]);
  const [payouts, setPayouts] = useState({ items: [], total: 0 });
  const [profile, setProfile] = useState(null);
  const [connected, setConnected] = useState(null);

  const role = user?.role || 'buyer';
  const canBuy = role === 'buyer' || role === 'both';
  const canSell = role === 'seller' || role === 'both' || role === 'admin';

  async function load() {
    try { setListings(await api('/listings/mine')); } catch {}
    try { setPurchases(await api('/orders/purchases')); } catch {}
    try { setSales(await api('/orders/sales')); } catch {}
    try { setBids(await api('/bids/mine')); } catch {}
    try { setIncoming(await api('/bids/incoming')); } catch {}
    try { setPayouts(await api('/payments/payouts')); } catch {}
    try { setConnected(await api('/payments/connect-status')); } catch {}
    if (user) {
      try { setProfile(await api(`/users/${user.id}`)); } catch {}
    }
  }
  useEffect(() => { if (user) load(); }, [user]);
  if (!user) return <p>Login required.</p>;

  async function deliver(id) {
    const o = await api(`/orders/${id}/deliver`, { method: 'POST' });
    alert(`Delivered. Buyer token: ${o.download_token}`);
    load();
  }
  async function confirm(id) {
    const o = await api(`/orders/${id}/confirm`, { method: 'POST' });
    alert(`Completed. Seller payout: $${o.payout_to_seller}`);
    load();
  }
  async function download(order) {
    const token = prompt('Download token (from seller delivery):', order.download_token || '');
    if (token === null) return;
    try {
      const access = localStorage.getItem('access_token');
      const res = await fetch(`${API_BASE}/orders/${order.id}/download?token=${encodeURIComponent(token)}`, {
        headers: access ? { Authorization: `Bearer ${access}` } : {},
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try { msg = (await res.json()).detail || msg; } catch {}
        throw new Error(msg);
      }
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        const j = await res.json();
        const url = j.file_url.startsWith('/') ? `${API_BASE}${j.file_url}` : j.file_url;
        window.open(url, '_blank');
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `project-${order.id.slice(0, 8)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (e) { alert(e.message); }
  }

  const spent = purchases.filter(o => o.status !== 'refunded').reduce((a, o) => a + o.amount, 0);
  const activeBids = bids.filter(b => b.status === 'pending' || b.status === 'countered').length;
  const escrow = sales.filter(o => o.status === 'paid' || o.status === 'delivered')
                      .reduce((a, o) => a + (o.amount - (o.fee || 0)), 0);
  const needShip = sales.filter(o => o.status === 'paid').length;

  return (
    <div>
      <div className="dash-head">
        <div>
          <h2>{role === 'seller' ? 'Seller Studio' : role === 'buyer' ? 'My Orders' : 'Dashboard'}</h2>
          <p className="muted">Hey {user.name} <span className={`role-pill ${role}`}>{role}</span></p>
        </div>
        {canSell && <Link to="/new" className="btn">+ New listing</Link>}
      </div>

      <div className="stat-row">
        {canBuy && <><div><strong>${spent.toFixed(0)}</strong><span>spent</span></div>
        <div><strong>{purchases.length}</strong><span>orders</span></div>
        <div><strong>{activeBids}</strong><span>active bids</span></div></>}
        {canSell && <><div><strong>${payouts.total.toFixed(2)}</strong><span>earned</span></div>
        <div><strong>${escrow.toFixed(2)}</strong><span>in escrow</span></div>
        <div><strong>{sales.length}</strong><span>sales</span></div>
        <div><strong>{listings.filter(l => l.status === 'active').length}</strong><span>live listings</span></div>
        <div><strong>★{profile?.rating ?? 0}</strong><span>seller rating</span></div></>}
      </div>

      {canSell && connected && !connected.connected && (
        <p className="error">Payouts not connected — <button onClick={async () => {
          const r = await api('/payments/connect-onboard', { method: 'POST' });
          alert(`Connect: ${JSON.stringify(r)}`); load();
        }}>Connect Stripe payouts</button></p>
      )}
      {canSell && needShip > 0 && (
        <p className="error">📦 {needShip} order{needShip > 1 ? 's' : ''} paid — deliver files to unlock payouts.</p>
      )}

      {canBuy && (
        <div className="section">
          <h3>🛒 Buying</h3>
          <h4>My Purchases ({purchases.length})</h4>
          {purchases.length === 0 && <p className="muted">Nothing bought yet — <Link to="/">browse projects</Link>.</p>}
          {purchases.map(o => (
            <div key={o.id} className="row-card">
              <span><Link to={`/l/${o.listing_id}`}>{o.listing_title || o.listing_id.slice(0, 8)}</Link> · ${o.amount} · {o.status}</span>
              <span>
                {o.status === 'delivered' && <button onClick={() => download(o)}>Download</button>}
                {o.status === 'delivered' && <button onClick={() => confirm(o.id)}>Confirm receipt</button>}
                {o.status === 'pending' && <button onClick={async () => { await api(`/orders/${o.id}/mock-pay`, { method: 'POST' }); load(); }}>Pay (mock)</button>}
                {o.status === 'completed' && <Link to={`/l/${o.listing_id}`}>Review</Link>}
              </span>
            </div>
          ))}
          <h4>My Bids ({bids.length})</h4>
          {bids.length === 0 && <p className="muted">No offers placed — bid on any listing with “Accept offers”.</p>}
          {bids.map(b => (
            <div key={b.id} className="row-card">
              <Link to={`/l/${b.listing_id}`}>{b.listing_id.slice(0, 8)}</Link>
              <span>${b.amount} · {b.status}{b.counter ? ` (counter $${b.counter})` : ''}</span>
            </div>
          ))}
        </div>
      )}

      {canSell && (
        <div className="section">
          <h3>🏪 Selling</h3>
          <h4>My Listings ({listings.length})</h4>
          {listings.length === 0 && <p className="muted">No listings yet — <Link to="/new">publish your first project</Link>.</p>}
          {listings.map(l => (
            <div key={l.id} className="row-card">
              <Link to={`/l/${l.id}`}>{l.title}</Link>
              <span>${l.price} · {l.status} · 👁 {l.views} <Link to={`/edit/${l.id}`}>Edit</Link>
                {l.status !== 'removed' && <button onClick={async () => {
                  if (!window.confirm(`Delete "${l.title}"? It will be hidden from the marketplace.`)) return;
                  try { await api(`/listings/${l.id}`, { method: 'DELETE' }); load(); }
                  catch (e) { alert(e.message); }
                }}>Delete</button>}
              </span>
            </div>
          ))}
          <h4>Incoming Offers ({incoming.length})</h4>
          {incoming.length === 0 && <p className="muted">No pending offers. Buyers can bid on listings with “Accept offers” on.</p>}
          {incoming.map(b => (
            <div key={b.id} className="row-card">
              <Link to={`/l/${b.listing_id}`}>{b.listing_title || b.listing_id.slice(0, 8)}</Link>
              <span>
                ${b.amount} · {b.status}
                <button onClick={async () => { await api(`/bids/${b.id}/accept`, { method: 'POST' }); load(); }}>Accept</button>
                <button onClick={async () => { await api(`/bids/${b.id}/reject`, { method: 'POST' }); load(); }}>Reject</button>
              </span>
            </div>
          ))}
          <h4>Incoming Orders ({sales.length})</h4>
          {sales.map(o => (
            <div key={o.id} className="row-card">
              <span><Link to={`/l/${o.listing_id}`}>{o.listing_title || o.listing_id.slice(0, 8)}</Link> · ${o.amount} · {o.status}</span>
              <span>
                {o.status === 'paid' && <button onClick={() => deliver(o.id)}>Deliver files</button>}
                {(o.status === 'paid' || o.status === 'delivered') && <button onClick={async () => { await api(`/orders/${o.id}/dispute`, { method: 'POST' }); load(); }}>Dispute</button>}
              </span>
            </div>
          ))}
          <h4>Payouts (total ${payouts.total})</h4>
          {payouts.items.map((p, i) => <p key={i} className="muted">Order {p.order_id.slice(0, 8)}: ${p.amount} (fee ${p.fee})</p>)}
          <button onClick={async () => { const t = await api('/payments/tax-doc'); alert(JSON.stringify(t)); }}>Tax document</button>
        </div>
      )}
    </div>
  );
}
