import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { API_BASE, api } from '../api';
import { useAuth } from '../AuthContext';

const img = (u) => (u && u.startsWith('/') ? `${API_BASE}${u}` : u);

function ProjectCard({ p, sold }) {
  return (
    <Link to={`/l/${p.id}`} className="card">
      {p.images?.[0] && <img src={img(p.images[0])} alt="" loading="lazy" />}
      <h4>{p.title}</h4>
      <p className="muted">{p.category}</p>
      <strong>${p.price}</strong>
      <span className={sold ? 'sold-tag' : 'muted'}>{sold ? ` · SOLD${p.sold_at ? ` · ${p.sold_at.slice(0, 10)}` : ''}` : ` · 👁 ${p.views ?? 0} · ★${p.rating ?? 0}`}</span>
    </Link>
  );
}

export function SellerProfile() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [following, setFollowing] = useState(false);
  const { user } = useAuth();

  useEffect(() => { api(`/users/${id}`).then(setP).catch(() => {}); }, [id]);
  if (!p) return <p>Loading...</p>;

  return (
    <div className="seller-page">
      <div className="seller-hero">
        {p.avatar
          ? <img src={p.avatar} alt="" className="seller-avatar" />
          : <div className="seller-avatar fallback">{p.name[0]}</div>}
        <div>
          <h2>{p.name} <span className={`role-pill ${p.role}`}>{p.role}</span> {p.badges?.map(b => <small key={b} className="badge">✓{b}</small>)} {p.flagged_seller ? <small className="badge warn">flagged ({p.strikes} reports)</small> : null}</h2>
      <p className="muted">{p.bio}</p>
      {!!(p.interests || []).length && <p className="muted">Looking for: {(p.interests || []).join(', ')}</p>}
          <p className="muted">Skills: {(p.skills || []).join(', ') || '—'}
            {p.github ? <span> · <a href={`https://github.com/${p.github}`} target="_blank" rel="noreferrer">GitHub: {p.github}</a></span> : null}
          </p>
          {user && user.id !== id && (
            <button onClick={async () => {
              const r = await api(`/users/${id}/follow`, { method: 'POST' });
              setFollowing(r.following);
              setP({ ...p, followers: p.followers + (r.following ? 1 : -1) });
            }}>{following ? 'Unfollow' : 'Follow'}</button>
          )}
        </div>
      </div>

      <div className="stat-row">
        <div><strong>{p.ongoing_count ?? 0}</strong><span>ongoing</span></div>
        <div><strong>{p.sold_count ?? 0}</strong><span>sold</span></div>
        <div><strong>${p.total_earned ?? 0}</strong><span>earned</span></div>
        <div><strong>★{p.rating ?? 0}</strong><span>({p.rating_count ?? 0} reviews{ p.rating_weighted ? `, weighted ${p.rating_weighted}` : ''})</span></div>
        <div><strong>{p.followers ?? 0}</strong><span>followers</span></div>
      </div>

      {p.role === 'buyer' ? (
        <p className="muted">Buyer account — no shop. {user && user.id === id ? 'Switch your role to seller in Profile to start selling.' : ''}</p>
      ) : (<>
      <h3>Ongoing projects ({(p.ongoing_projects || []).length})</h3>
      {(p.ongoing_projects || []).length === 0 && <p className="muted">No ongoing projects right now.</p>}
      <div className="grid">
        {(p.ongoing_projects || []).map(l => <ProjectCard key={l.id} p={l} />)}
      </div>

      <h3>Sold ({(p.sold_projects || []).length})</h3>
      {(p.sold_projects || []).length === 0 && <p className="muted">Nothing sold yet.</p>}
      <div className="grid">
        {(p.sold_projects || []).map(l => <ProjectCard key={l.id} p={l} sold />)}
      </div>
      </>)}
    </div>
  );
}
