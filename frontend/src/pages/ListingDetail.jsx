import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';
import { Bids } from './Bids';
import { Reviews } from './Reviews';

function img(u) {
  if (!u) return '';
  return u.startsWith('/') ? `${API_BASE}${u}` : u;
}

export function ListingDetail() {
  const { id } = useParams();
  const [l, setL] = useState(null);
  const [related, setRelated] = useState([]);
  const [err, setErr] = useState('');
  const [myOrder, setMyOrder] = useState(null);
  const [pastOrder, setPastOrder] = useState(null);
  const { user } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    api(`/listings/${id}`).then(setL).catch(e => setErr(String(e.message)));
    api(`/listings/${id}/related`).then(setRelated).catch(() => {});
    if (user) {
      // any prior order of mine for this listing → Purchased badge + review when completed
      api('/orders/purchases').then(os => {
        const mine = os.filter(o => o.listing_id === id).sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
        if (mine.length) setPastOrder(mine.find(o => o.status === 'completed') || mine[0]);
      }).catch(() => {});
    }
  }, [id, user]);

  async function buy() {
    if (!user) return nav('/login');
    if (!window.confirm(`Buy "${l.title}" for $${l.price}?`)) return;
    try {
      const order = await api('/orders', { method: 'POST', body: JSON.stringify({ listing_id: id }) });
      setMyOrder(order);
      // Mock mode: simulate payment immediately. Live mode: confirm with Stripe.js using client_secret.
      if (order.stripe_mode === 'mock') {
        await api(`/orders/${order.id}/mock-pay`, { method: 'POST' });
        alert('Payment successful (mock). See Dashboard > Purchases.');
        nav('/dashboard');
      } else {
        alert(`Stripe client_secret: ${order.client_secret}\nWire Stripe.js confirmCardPayment here.`);
      }
    } catch (e) { alert(e.message); }
  }

  async function ask() {
    if (!user) return nav('/login');
    const t = await api('/threads', { method: 'POST', body: JSON.stringify({ listing_id: id }) });
    nav(`/messages?thread=${t.id}`);
  }

  if (err) return <p className="error">{err}</p>;
  if (!l) return <p>Loading...</p>;
  return (
    <div>
      <h2>{l.title} {l.featured ? '⭐' : ''} {pastOrder ? <small className="badge">✓ purchased ({pastOrder.status})</small> : null} {l.flagged_duplicate ? <small className="error">(flagged: possible duplicate)</small> : null}</h2>
      <p className="muted">{l.category} · {l.tech_stack?.join(', ')} · 👁 {l.views} · seller ★{l.seller_rating || 0} ({l.seller_rating_count || 0}) · {l.status} · license: {l.license}</p>
      <div className="imgs">{l.images?.map((u, i) => <img key={i} src={img(u)} alt="" />)}</div>
      {l.demo_video && /^https?:\/\//.test(l.demo_video) && <p><a href={l.demo_video} target="_blank" rel="noreferrer">▶ Demo video</a></p>}
      <p>{l.description}</p>
      {!!l.pricing_tiers?.length && (
        <div>{l.pricing_tiers.map((t, i) => <p key={i} className="muted">{t.name}: ${t.price} — {t.description}</p>)}</div>
      )}
      {!!l.specs && Object.keys(l.specs).length > 0 && (
        <div className="specs">{Object.entries(l.specs).map(([k, v]) => <span key={k} className="spec">{k}: <strong>{v}</strong></span>)}</div>
      )}
      <h3>${l.price}</h3>
      {l.seller && <p>Seller: <Link to={`/u/${l.seller_id}`}>{l.seller.name}</Link></p>}
      <div className="row">
        {user && user.id === l.seller_id && <button className="btn" onClick={() => nav(`/edit/${id}`)}>Edit listing</button>}
        {(!user || user.id !== l.seller_id) && <button className="btn" onClick={buy}>Buy Now</button>}
        {(!user || user.id !== l.seller_id) && <button onClick={ask}>Ask a question</button>}
        <button onClick={async () => { const r = prompt('Reason (stolen/plagiarized?)'); if (r) { await api(`/listings/${id}/report`, { method: 'POST', body: JSON.stringify({ reason: r }) }); alert('Reported'); } }}>Report</button>
      </div>
      <Bids listingId={id} sellerId={l.seller_id} />
      <Reviews listingId={id} orderId={myOrder?.id || (pastOrder?.status === 'completed' ? pastOrder.id : null)} canReview={!!myOrder || pastOrder?.status === 'completed'} />
      {!!related.length && (
        <><h3>Related</h3><div className="grid">{related.map(r => (
          <Link key={r.id} to={`/l/${r.id}`} className="card"><h4>{r.title}</h4><p className="muted">${r.price}</p></Link>
        ))}</div></>
      )}
    </div>
  );
}
