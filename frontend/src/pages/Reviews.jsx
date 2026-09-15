import { useEffect, useState } from 'react';
import { api } from '../api';

export function Reviews({ listingId, orderId, canReview }) {
  const [items, setItems] = useState([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');

  async function load() {
    try { setItems(await api(`/listings/${listingId}/reviews`)); } catch {}
  }
  useEffect(() => { load(); }, [listingId]);

  async function submit() {
    await api(`/orders/${orderId}/reviews`, { method: 'POST', body: JSON.stringify({ rating: Number(rating), comment }) });
    setComment(''); load();
  }

  return (
    <div className="section">
      <h3>Reviews ({items.length})</h3>
      {items.map(r => (
        <div key={r.id} className="row-card">
          <span>{'★'.repeat(r.rating)} — {r.comment}{r.response ? <><br /><em>Seller: {r.response}</em></> : null}</span>
        </div>
      ))}
      {canReview && orderId && (
        <div className="row">
          <select value={rating} onChange={e => setRating(e.target.value)}>{[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n} stars</option>)}</select>
          <input placeholder="Comment" value={comment} onChange={e => setComment(e.target.value)} />
          <button onClick={submit}>Leave review</button>
        </div>
      )}
    </div>
  );
}
