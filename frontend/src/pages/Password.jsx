import { useState } from 'react';
import { api } from '../api';

export function Forgot() {
  const [email, setEmail] = useState('');
  const [msg, setMsg] = useState('');
  return (
    <div className="form">
      <h2>Forgot password</h2>
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <button className="btn" onClick={async () => {
        const r = await api('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });
        setMsg(`Reset token (dev): ${r.reset_token_dev} — use /reset page`);
      }}>Send reset link</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}

export function Reset() {
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');
  return (
    <div className="form">
      <h2>Reset password</h2>
      <input placeholder="Token" value={token} onChange={e => setToken(e.target.value)} />
      <input placeholder="New password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button className="btn" onClick={async () => {
        try { await api('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, password }) }); setMsg('Done — login now.'); }
        catch (e) { setMsg(e.message); }
      }}>Reset</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}

export function VerifyEmail() {
  const [token, setToken] = useState('');
  const [msg, setMsg] = useState('');
  return (
    <div className="form">
      <h2>Verify email</h2>
      <input placeholder="Token from signup response / email" value={token} onChange={e => setToken(e.target.value)} />
      <button className="btn" onClick={async () => {
        try { await api('/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) }); setMsg('Verified!'); }
        catch (e) { setMsg(e.message); }
      }}>Verify</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}
