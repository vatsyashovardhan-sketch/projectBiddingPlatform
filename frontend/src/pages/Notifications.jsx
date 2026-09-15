import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Notifications() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [prefs, setPrefs] = useState({});
  async function load() {
    const n = await api('/notifications');
    setItems(n.items);
    const p = await api('/notifications/prefs');
    setPrefs(p.opt_out || {});
  }
  useEffect(() => { if (user) load(); }, [user]);
  if (!user) return <p>Login required.</p>;
  return (
    <div>
      <h2>Notifications</h2>
      <button onClick={async () => { await api('/notifications/read-all', { method: 'POST' }); load(); }}>Mark all read</button>
      {items.map(n => (
        <div key={n.id} className="row-card">
          <span>{n.read ? '' : '● '}[{n.kind}] {n.title}</span>
          {!n.read && <button onClick={async () => { await api(`/notifications/${n.id}/read`, { method: 'POST' }); load(); }}>Read</button>}
        </div>
      ))}
      <h3>Preferences</h3>
      {['bid', 'order', 'message', 'review', 'system'].map(k => (
        <label key={k}><input type="checkbox" checked={!prefs[k]} onChange={async () => {
          const next = { ...prefs, [k]: !prefs[k] ? true : false };
          if (next[k] === false) delete next[k];
          await api('/notifications/prefs', { method: 'POST', body: JSON.stringify({ opt_out: next }) });
          load();
        }} /> {k} </label>
      ))}
    </div>
  );
}
