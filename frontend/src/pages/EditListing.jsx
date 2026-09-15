import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api';

export function EditListing() {
  const { id } = useParams();
  const nav = useNavigate();
  const [form, setForm] = useState(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api(`/listings/${id}`).then(l => setForm({
      title: l.title, description: l.description, price: l.price, category: l.category,
      tech_stack: (l.tech_stack || []).join(','), demo_video: l.demo_video || '',
      license: l.license || 'personal', accept_offers: l.accept_offers !== false,
      status: l.status,
    })).catch(e => setMsg(e.message));
  }, [id]);

  async function save() {
    try {
      await api(`/listings/${id}`, { method: 'PATCH', body: JSON.stringify({
        ...form, price: Number(form.price),
        tech_stack: form.tech_stack.split(',').map(s => s.trim()).filter(Boolean),
      }) });
      nav(`/l/${id}`);
    } catch (e) { setMsg(e.message); }
  }

  if (!form) return <p>{msg || 'Loading...'}</p>;
  return (
    <div className="form wide">
      <h2>Edit listing</h2>
      {msg && <p className="error">{msg}</p>}
      <input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
      <textarea rows={5} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
      <div className="row">
        <input type="number" min={1} value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} />
        <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="sold">Sold</option>
          <option value="removed">Removed</option>
        </select>
        <select value={form.license} onChange={e => setForm({ ...form, license: e.target.value })}>
          <option value="personal">personal use</option>
          <option value="resale">resale allowed</option>
          <option value="exclusive">exclusive</option>
        </select>
      </div>
      <input placeholder="Tech stack (comma separated)" value={form.tech_stack} onChange={e => setForm({ ...form, tech_stack: e.target.value })} />
      <input placeholder="Demo video URL" value={form.demo_video} onChange={e => setForm({ ...form, demo_video: e.target.value })} />
      <label><input type="checkbox" checked={form.accept_offers} onChange={e => setForm({ ...form, accept_offers: e.target.checked })} /> Accept offers</label>
      <div className="row">
        <button className="btn" onClick={save}>Save changes</button>
        <button onClick={async () => {
          if (!window.confirm(`Delete "${form.title}"? It will be hidden from the marketplace.`)) return;
          try { await api(`/listings/${id}`, { method: 'DELETE' }); nav('/dashboard'); }
          catch (e) { setMsg(e.message); }
        }}>Delete project</button>
      </div>
    </div>
  );
}
