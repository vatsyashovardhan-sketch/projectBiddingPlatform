import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Admin() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [reports, setReports] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        setStats(await api('/admin/stats'));
        setUsers(await api('/admin/users'));
        setOrders(await api('/admin/orders'));
        setReports(await api('/admin/reports'));
      } catch {}
    })();
  }, []);
  if (!user) return <p>Login required.</p>;
  if (user.role !== 'admin') return <p>Admin only. (Set your role to "admin" via PATCH /users/me.)</p>;

  return (
    <div>
      <h2>Admin</h2>
      {stats && <p className="muted">Users {stats.users} · Listings {stats.listings} · Orders {stats.orders} · GMV ${stats.gmv} · {JSON.stringify(stats.orders_by_status)}</p>}
      <h3>Disputes / orders</h3>
      {orders.filter(o => o.status === 'disputed').map(o => (
        <div key={o._id} className="row-card">
          <span>{o._id.slice(0, 8)} · ${o.amount}</span>
          <span>
            <button onClick={async () => { await api(`/admin/orders/${o._id}/resolve`, { method: 'POST', body: JSON.stringify({ action: 'refund' }) }); alert('refunded'); }}>Refund buyer</button>
            <button onClick={async () => { await api(`/admin/orders/${o._id}/resolve`, { method: 'POST', body: JSON.stringify({ action: 'release' }) }); alert('released'); }}>Release to seller</button>
          </span>
        </div>
      ))}
      <h3>Users</h3>
      {users.map(u => (
        <div key={u.id} className="row-card">
          <span>{u.email} · {u.role} {u.banned ? '(banned)' : ''}</span>
          <button onClick={async () => { await api(`/admin/users/${u.id}/ban`, { method: 'POST', body: JSON.stringify({ banned: !u.banned }) }); }}>Toggle ban</button>
        </div>
      ))}
      <h3>Moderation queue ({reports.length})</h3>
      {reports.map((r, i) => <p key={i} className="muted">{r.type}: {r.target} — {r.reason} (by {r.by})</p>)}
      <button onClick={async () => { const r = await api('/jobs/run', { method: 'POST' }); alert(JSON.stringify(r)); }}>Run expiry jobs</button>
    </div>
  );
}
