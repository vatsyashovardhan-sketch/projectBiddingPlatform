import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export function Sellers() {
  const [sellers, setSellers] = useState([]);
  useEffect(() => { api('/users/sellers/top?limit=40').then(setSellers).catch(() => {}); }, []);
  return (
    <div>
      <h2>Sellers ({sellers.length})</h2>
      <div className="grid">
        {sellers.map(s => (
          <Link key={s.id} to={`/u/${s.id}`} className="card seller-card">
            <div className="seller-mini">
              {s.avatar ? <img src={s.avatar} alt="" className="mini-avatar" /> : <div className="mini-avatar fallback">{s.name[0]}</div>}
              <div>
                <h4>{s.name} {s.badges?.map(b => <small key={b}>✓{b}</small>)}</h4>
                <p className="muted">★{s.rating} ({s.rating_count}) · {s.followers} followers</p>
              </div>
            </div>
            <p className="muted">{s.ongoing_count} ongoing · {s.sold_count} sold</p>
            <p className="muted skills">{(s.skills || []).slice(0, 4).join(' · ')}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
