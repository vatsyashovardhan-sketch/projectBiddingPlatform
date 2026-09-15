import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');
  const { login } = useAuth();
  const nav = useNavigate();
  return (
    <div className="form">
      <h2>Login</h2>
      {err && <p className="error">{err}</p>}
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button className="btn" onClick={async () => {
        try { await login(email, password); nav('/'); } catch (e) { setErr(e.message); }
      }}>Login</button>
      <p className="muted"><Link to="/forgot">Forgot password?</Link> · <Link to="/verify-email">Verify email</Link></p>
      <button onClick={async () => {
        const r = await api('/auth/oauth/callback', { method: 'POST', body: JSON.stringify({ email: email || 'dev@test.com', name: 'GitHub User', github: 'octocat' }) });
        localStorage.setItem('access_token', r.access_token); localStorage.setItem('refresh_token', r.refresh_token);
        window.location.href = '/';
      }}>Continue with GitHub (mock)</button>
    </div>
  );
}

export function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('both');
  const [err, setErr] = useState('');
  const { signup } = useAuth();
  const nav = useNavigate();
  return (
    <div className="form">
      <h2>Sign up</h2>
      {err && <p className="error">{err}</p>}
      <input placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
      <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input placeholder="Password (8+ chars, letter+number)" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <select value={role} onChange={e => setRole(e.target.value)}>
        <option value="both">Buyer + Seller</option>
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
      </select>
      <button className="btn" onClick={async () => {
        try { await signup(email, password, name, role); nav('/'); } catch (e) { setErr(e.message); }
      }}>Create account</button>
    </div>
  );
}

export function Profile() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({ name: user?.name || '', bio: user?.bio || '', role: user?.role || 'both', skills: (user?.skills || []).join(','), github: user?.github || '', portfolio: (user?.portfolio || []).join(','), interests: (user?.interests || []).join(',') });
  const [msg, setMsg] = useState('');
  if (!user) return <p>Login required.</p>;
  const isBuyer = form.role === 'buyer' || form.role === 'both';
  const isSeller = form.role === 'seller' || form.role === 'both';
  return (
    <div className="form">
      <h2>{isSeller && !isBuyer ? 'Seller profile' : isBuyer && !isSeller ? 'Buyer profile' : 'Edit profile'} {user.badges?.map(b => <small key={b}>✓{b}</small>)}</h2>
      <input placeholder="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
      <textarea placeholder="Bio" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} />
      {isBuyer && (
        <input placeholder="Looking for (comma separated: ML projects, flutter apps)" value={form.interests} onChange={e => setForm({ ...form, interests: e.target.value })} />
      )}
      {isSeller && (<>
        <input placeholder="Skills (comma separated)" value={form.skills} onChange={e => setForm({ ...form, skills: e.target.value })} />
        <input placeholder="GitHub username" value={form.github} onChange={e => setForm({ ...form, github: e.target.value })} />
        <input placeholder="Portfolio links (comma separated)" value={form.portfolio} onChange={e => setForm({ ...form, portfolio: e.target.value })} />
      </>)}
      <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
        <option value="both">Buyer + Seller</option>
        <option value="buyer">Buyer</option>
        <option value="seller">Seller</option>
      </select>
      <button className="btn" onClick={async () => {
        const body = { ...form, skills: form.skills.split(',').map(s => s.trim()).filter(Boolean), portfolio: form.portfolio.split(',').map(s => s.trim()).filter(Boolean), interests: form.interests.split(',').map(s => s.trim()).filter(Boolean) };
        const me = await api('/users/me', { method: 'PATCH', body: JSON.stringify(body) });
        setUser(me); localStorage.setItem('user', JSON.stringify(me)); setMsg('Saved!');
      }}>Save</button>
      {msg && <p>{msg}</p>}
      {isSeller && (<>
      <button onClick={async () => {
        const r = await api('/payments/connect-onboard', { method: 'POST' });
        alert(`Connect: ${JSON.stringify(r)}`);
      }}>Connect Stripe payout account</button>
      <button onClick={async () => {
        const edu = prompt('Student email (.edu):'); if (!edu) return;
        const r = await api('/users/me/request-student-badge', { method: 'POST', body: JSON.stringify({ edu_email: edu }) });
        alert(JSON.stringify(r));
      }}>Verify student badge</button>
      <button onClick={async () => {
        const r = await api('/users/me/link-github', { method: 'POST', body: JSON.stringify({ github: form.github }) });
        alert(JSON.stringify(r));
      }}>Link GitHub (developer badge)</button>
      </>)}
      {isSeller && !isBuyer && (
        <p className="muted">Public storefront: <a href={`/u/${user.id}`}>view my shop</a></p>
      )}
      <button onClick={async () => {
        const r = await api('/auth/2fa/enable', { method: 'POST' });
        const code = prompt(`2FA setup: ${r.otpauth_url}\nEnter 6-digit code:`); if (!code) return;
        await api('/auth/2fa/verify', { method: 'POST', body: JSON.stringify({ code }) });
        alert('2FA enabled');
      }}>Enable 2FA</button>
    </div>
  );
}
