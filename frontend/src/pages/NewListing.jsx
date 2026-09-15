import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

export function NewListing() {
  const [cats, setCats] = useState([]);
  const [form, setForm] = useState({ title: '', description: '', price: 49, category: 'Web App', tech_stack: '', status: 'active', demo_video: '', license: 'personal', accept_offers: true, tiers: '', specs: '' });
  const [images, setImages] = useState([]);
  const [fileKey, setFileKey] = useState('');
  const [fileHash, setFileHash] = useState('');
  const [err, setErr] = useState('');
  const { user } = useAuth();
  const nav = useNavigate();

  useEffect(() => { api('/listings/categories').then(d => setCats(d.categories)).catch(() => {}); }, []);

  async function uploadPreview(e) {
    const f = e.target.files[0];
    if (!f) return;
    setErr('');
    try {
      const fd = new FormData();
      fd.append('file', f);
      const r = await api('/uploads/preview', { method: 'POST', body: fd });
      setImages([...images, r.url]);
    } catch (ex) { setErr(ex.message); }
  }

  async function uploadZip(e) {
    const f = e.target.files[0];
    if (!f) return;
    setErr('');
    try {
      const fd = new FormData();
      fd.append('file', f);
      const r = await api('/uploads/project-file', { method: 'POST', body: fd });
      setFileKey(r.key);
      setFileHash(r.file_hash || '');
      if (r.duplicate_warning) alert('Warning: identical file already exists (possible duplicate)');
    } catch (ex) { setErr(ex.message); }
  }

  async function submit() {
    setErr('');
    if (!user) { setErr('Login required.'); return; }
    if (user.role === 'buyer') { setErr('A seller account is required to publish. Change role in Profile.'); return; }
    if ((form.title || '').length < 3 || (form.description || '').length < 10) {
      setErr('Title (3+) and description (10+) are too short.');
      return;
    }
    const tiers = form.tiers.split(';').map(s => s.trim()).filter(Boolean).map(s => {
      const [name, price] = s.split(':');
      return { name: (name || '').trim(), price: Number(price || 0), description: '' };
    }).filter(t => t.name && t.price > 0);
    const specs = {};
    form.specs.split(';').map(s => s.trim()).filter(Boolean).forEach(s => {
      const i = s.indexOf(':');
      if (i > 0) specs[s.slice(0, i).trim()] = s.slice(i + 1).trim();
    });
    const body = {
      ...form,
      price: Number(form.price),
      tech_stack: form.tech_stack.split(',').map(s => s.trim()).filter(Boolean),
      images,
      project_file: fileKey,
      file_hash: fileHash,
      pricing_tiers: tiers,
      specs,
    };
    delete body.tiers;
    try {
      const l = await api('/listings', { method: 'POST', body: JSON.stringify(body) });
      if (l.duplicate_warning) alert('Duplicate file detected — listing flagged for review');
      nav(`/l/${l.id}`);
    } catch (e) { setErr(e.message); }
  }

  const img = (u) => (u.startsWith('/') ? `${API_BASE}${u}` : u);

  return (
    <div className="form wide">
      <h2>Sell a project</h2>
      {user?.role === 'buyer' && <p className="error">Buyer accounts can't publish. Switch role to seller in Profile.</p>}
      {err && <p className="error">{err}</p>}
      <input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
      <textarea placeholder="Description (min 10 chars)" rows={5} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
      <div className="row">
        <input type="number" min={1} value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} />
        <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
          {cats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <input placeholder="Tech stack (comma separated: react, python)" value={form.tech_stack} onChange={e => setForm({ ...form, tech_stack: e.target.value })} />
      <input placeholder="Demo video URL (YouTube/Loom)" value={form.demo_video} onChange={e => setForm({ ...form, demo_video: e.target.value })} />
      <div className="row">
        <select value={form.license} onChange={e => setForm({ ...form, license: e.target.value })}>
          <option value="personal">License: personal use</option>
          <option value="resale">License: resale allowed</option>
          <option value="exclusive">License: exclusive one-time sale</option>
        </select>
        <label><input type="checkbox" checked={form.accept_offers} onChange={e => setForm({ ...form, accept_offers: e.target.checked })} /> Accept offers</label>
      </div>
      <input placeholder="Pricing tiers (name:price; ...) e.g. code only:29; code+docs:49" value={form.tiers} onChange={e => setForm({ ...form, tiers: e.target.value })} />
      <input placeholder="Category specs (key:value; ...) e.g. dataset size:10k rows; accuracy:94%" value={form.specs} onChange={e => setForm({ ...form, specs: e.target.value })} />
      <label>Screenshots: <input type="file" accept="image/*" onChange={uploadPreview} /></label>
      <div className="imgs">{images.map((u, i) => <img key={i} src={img(u)} alt="" />)}</div>
      <label>Project .zip (locked until purchase): <input type="file" accept=".zip" onChange={uploadZip} /></label>
      {fileKey && <p className="muted">Attached: {fileKey}</p>}
      <button className="btn" onClick={submit}>Publish listing</button>
    </div>
  );
}
