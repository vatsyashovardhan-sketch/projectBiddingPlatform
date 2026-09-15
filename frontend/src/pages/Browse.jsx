import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

function img(u) {
  if (!u) return '';
  return u.startsWith('/') ? `${API_BASE}${u}` : u;
}

export function Browse() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [tech, setTech] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [sort, setSort] = useState('newest');
  const [cats, setCats] = useState([]);
  const [tags, setTags] = useState([]);
  const [minRating, setMinRating] = useState('');
  const [bidsOnly, setBidsOnly] = useState(false);
  const [featured, setFeatured] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();

  // "Picks for you": match buyer interests against category/tech (client-side, from loaded items)
  const picks = user && (user.interests || []).length
    ? items.filter(l => (user.interests || []).some(k => {
        const kw = k.toLowerCase();
        return l.category.toLowerCase().includes(kw) || (l.tech_stack || []).some(t => t.toLowerCase().includes(kw));
      })).slice(0, 4)
    : [];

  async function load(over = {}) {
    setLoading(true);
    setError('');
    try {
      const f = { q, category, tech, minPrice, maxPrice, sort, minRating, bidsOnly, ...over };
      const p = new URLSearchParams({ page: 1, limit: 24, sort: f.sort });
      if (f.q) p.set('q', f.q);
      if (f.category) p.set('category', f.category);
      if (f.tech) p.set('tech', f.tech);
      if (f.minPrice !== '') p.set('min_price', f.minPrice);
      if (f.maxPrice !== '') p.set('max_price', f.maxPrice);
      if (f.minRating) p.set('min_rating', f.minRating);
      if (f.bidsOnly) p.set('open_to_bids', 'true');
      const data = await api(`/listings?${p.toString()}`);
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // initial data (static lists once)
  useEffect(() => {
    api('/listings/categories').then(d => setCats(d.categories)).catch(() => {});
    api('/listings/tags').then(d => setTags(d.tags)).catch(() => {});
    api('/listings/featured').then(setFeatured).catch(() => {});
    api('/listings/trending').then(setTrending).catch(() => {});
    load();
    // eslint-disable-next-line
  }, []);

  // auto-apply when dropdowns/checkbox change (pass fresh values explicitly)
  const auto = (patch) => {
    if (patch.category !== undefined) setCategory(patch.category);
    if (patch.sort !== undefined) setSort(patch.sort);
    if (patch.minRating !== undefined) setMinRating(patch.minRating);
    if (patch.bidsOnly !== undefined) setBidsOnly(patch.bidsOnly);
    if (patch.tech !== undefined) setTech(patch.tech);
    load(patch);
  };

  // debounce free-text search + price
  useEffect(() => {
    const t = setTimeout(() => load(), 450);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [q, minPrice, maxPrice]);

  function clear() {
    setQ(''); setCategory(''); setTech(''); setMinPrice(''); setMaxPrice('');
    setSort('newest'); setMinRating(''); setBidsOnly(false);
    load({ q: '', category: '', tech: '', minPrice: '', maxPrice: '', sort: 'newest', minRating: '', bidsOnly: false });
  }

  return (
    <div>
      {!user && (
        <div className="hero">
          <h2>Buy & sell student projects</h2>
          <p className="muted">Browse freely — login to bid, buy, or sell your own work.</p>
          <div className="row">
            <Link to="/login" className="btn">Login</Link>
            <Link to="/signup" className="btn secondary">Sign up free</Link>
          </div>
        </div>
      )}
      {user?.role === 'seller' && (
        <div className="hero seller">
          <h2>Your shop is open 🏪</h2>
          <p className="muted">List a new project or check incoming orders.</p>
          <div className="row">
            <Link to="/new" className="btn">+ Sell a project</Link>
            <Link to="/dashboard" className="btn secondary">My Shop</Link>
          </div>
        </div>
      )}
      {user?.role === 'buyer' && (
        <div className="hero buyer">
          <h2>Find your next project 🛒</h2>
          <p className="muted">Bid on open listings or buy instantly — track it all in My Orders.</p>
          <div className="row">
            <Link to="/dashboard" className="btn">My Orders</Link>
            <Link to="/sellers" className="btn secondary">Top sellers</Link>
          </div>
        </div>
      )}
      {!!featured.length && (
        <><h2>Featured</h2><div className="grid">
          {featured.map(l => (
            <Link key={l.id} to={`/l/${l.id}`} className="card feat">
              {l.images?.[0] && <img src={img(l.images[0])} alt="" />}
              <h3>⭐ {l.title}</h3>
              <p className="muted">{l.category} · ★{l.rating} · ${l.price}</p>
            </Link>
          ))}
        </div></>
      )}
      <h2>Browse projects ({total})</h2>
      {!!picks.length && (
        <><h3>Picks for you</h3><div className="grid">
          {picks.map(l => (
            <Link key={l.id} to={`/l/${l.id}`} className="card feat">
              {l.images?.[0] && <img src={img(l.images[0])} alt="" />}
              <h3>✨ {l.title}</h3>
              <p className="muted">{l.category} · ${l.price}</p>
            </Link>
          ))}
        </div></>
      )}
      <div className="filters">
        <input placeholder="Search title/description..." value={q} onChange={e => setQ(e.target.value)} />
        <select value={category} onChange={e => auto({ category: e.target.value })}>
          <option value="">All categories</option>
          {cats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input placeholder="Tech (e.g. react)" list="taglist" value={tech} onChange={e => setTech(e.target.value)} onBlur={e => load({ tech: e.target.value })} />
        <datalist id="taglist">{tags.map(t => <option key={t} value={t} />)}</datalist>
        <input type="number" min={0} placeholder="Min $" value={minPrice} onChange={e => setMinPrice(e.target.value)} />
        <input type="number" min={0} placeholder="Max $" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} />
        <select value={sort} onChange={e => auto({ sort: e.target.value })}>
          <option value="newest">Newest</option>
          <option value="price_asc">Price low-high</option>
          <option value="price_desc">Price high-low</option>
          <option value="popular">Most viewed</option>
          <option value="rating">Top rated</option>
        </select>
        <select value={minRating} onChange={e => auto({ minRating: e.target.value })}>
          <option value="">Any seller rating</option>
          <option value="4">Seller 4★+</option>
          <option value="3">Seller 3★+</option>
        </select>
        <label><input type="checkbox" checked={bidsOnly} onChange={e => auto({ bidsOnly: e.target.checked })} /> open to bids</label>
        <button onClick={() => load()}>Search</button>
        <button className="btn secondary" onClick={clear}>Clear</button>
      </div>
      {loading && <p className="muted">Loading…</p>}
      {error && <p className="error">{error} <button onClick={() => load()}>Retry</button></p>}
      {!loading && !error && items.length === 0 && <p className="muted">No projects match — try clearing filters.</p>}
      <div className="grid">
        {items.map(l => (
          <Link key={l.id} to={`/l/${l.id}`} className="card">
            {l.images?.[0] && <img src={img(l.images[0])} alt="" />}
            <h3>{l.title}</h3>
            <p className="muted">{l.category} · {l.tech_stack?.join(', ')}</p>
            <strong>${l.price}</strong>
            <span className="muted"> · 👁 {l.views} · ★{l.seller_rating || l.rating || 0}</span>
          </Link>
        ))}
      </div>
      {!!trending.length && (
        <><h3>Trending this week</h3><p className="muted">{trending.slice(0, 5).map(t => t.title).join(' · ')}</p></>
      )}
    </div>
  );
}
