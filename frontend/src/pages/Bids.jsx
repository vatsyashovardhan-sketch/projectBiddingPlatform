import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Bids({ listingId, sellerId }) {
  const { user } = useAuth();
  const [bids, setBids] = useState([]);
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');
  const [mine, setMine] = useState([]);
  const [stats, setStats] = useState(null);
  const isSeller = user && user.id === sellerId;

  async function load() {
    if (isSeller) {
      try { setBids(await api(`/listings/${listingId}/bids`)); } catch {}
      try { setStats(await api('/bids/analytics')); } catch {}
    }
    if (user) {
      try { setMine(await api('/bids/mine')); } catch {}
    }
  }
  useEffect(() => { load(); }, [listingId]);

  async function place() {
    await api(`/listings/${listingId}/bids`, { method: 'POST', body: JSON.stringify({ amount: Number(amount), message }) });
    setAmount(''); setMessage(''); load();
  }
  async function act(id, action, counter) {
    const body = action === 'counter' ? { amount: Number(prompt('Counter amount:')) } : {};
    await api(`/bids/${id}/${action}`, { method: 'POST', body: JSON.stringify(body) });
    load();
  }

  return (
    <div className="section">
      <h3>Offers {stats ? <small className="muted">({stats.total_bids} bids, {stats.accepted} accepted, avg ${stats.avg_accepted})</small> : null}</h3>
      {!isSeller && (
        <div className="row">
          <input type="number" placeholder="Your offer $" value={amount} onChange={e => setAmount(e.target.value)} />
          <input placeholder="Message (optional)" value={message} onChange={e => setMessage(e.target.value)} />
          <button onClick={place}>Place bid</button>
        </div>
      )}
      {isSeller && bids.map(b => (
        <div key={b.id} className="row-card">
          <span>${b.amount} {b.counter ? `(counter $${b.counter})` : ''} · {b.status} · {b.message}</span>
          <span>
            <button onClick={() => act(b.id, 'accept')}>Accept</button>
            <button onClick={() => act(b.id, 'reject')}>Reject</button>
            <button onClick={() => act(b.id, 'counter')}>Counter</button>
          </span>
        </div>
      ))}
      {!isSeller && mine.filter(b => b.listing_id === listingId).map(b => (
        <p key={b.id} className="muted">Your bid: ${b.amount} — {b.status}{b.counter ? ` (counter $${b.counter})` : ''}</p>
      ))}
    </div>
  );
}
