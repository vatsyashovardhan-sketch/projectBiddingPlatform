import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Messages() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const [threads, setThreads] = useState([]);
  const [unread, setUnread] = useState(0);
  const [active, setActive] = useState(() => params.get('thread'));
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState('');

  async function loadThreads() {
    const d = await api('/threads');
    setThreads(d.threads); setUnread(d.unread_total);
    const want = params.get('thread');
    if (want && d.threads.some(t => t.id === want)) { setActive(want); return; }
    if (!active && d.threads[0]) setActive(d.threads[0].id);
  }
  async function loadMsgs() {
    if (!active) return;
    setMsgs(await api(`/threads/${active}/messages`));
  }
  useEffect(() => { if (user) { loadThreads(); const t = setInterval(loadThreads, 8000); return () => clearInterval(t); } }, [user]);
  useEffect(() => { loadMsgs(); const t = setInterval(loadMsgs, 4000); return () => clearInterval(t); }, [active]);

  async function send() {
    await api(`/threads/${active}/messages`, { method: 'POST', body: JSON.stringify({ text }) });
    setText(''); loadMsgs();
  }
  if (!user) return <p>Login required.</p>;
  return (
    <div>
      <h2>Messages {unread ? `(${unread} unread)` : ''}</h2>
      <div className="msgs">
        <div className="thread-list">
          {threads.map(t => (
            <button key={t.id} className={t.id === active ? 'active' : ''} onClick={() => setActive(t.id)}>
              {(t.unread_buyer + t.unread_seller) > 0 ? '● ' : ''}{t.listing_id.slice(0, 8) || t.order_id.slice(0, 8)}
            </button>
          ))}
        </div>
        <div className="chat">
          {msgs.map((m, i) => <p key={i}><strong>{m.from === user.id ? 'You' : 'Them'}:</strong> {m.text}</p>)}
          {active && (
            <div className="row">
              <input placeholder="Message..." value={text} onChange={e => setText(e.target.value)} />
              <button onClick={send}>Send</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
