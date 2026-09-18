import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { api } from './api';

export function Nav() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [unread, setUnread] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  useEffect(() => {
    if (!user) return;
    api('/notifications').then(n => setUnread(n.unread)).catch(() => {});
    const t = setInterval(() => api('/notifications').then(n => setUnread(n.unread)).catch(() => {}), 15000);
    return () => clearInterval(t);
  }, [user]);
  const role = user?.role;
  const canSell = role === 'seller' || role === 'both' || role === 'admin';
  const dashLabel = role === 'buyer' ? 'My Orders' : role === 'seller' ? 'My Shop' : 'Dashboard';
  return (
    <nav className={`nav${scrolled ? ' scrolled' : ''}`}>
      <Link to="/" className="brand">ProjectBidding</Link>
      <div className="links">
        <Link to="/">Browse</Link>
        <Link to="/sellers">Sellers</Link>
        {user && canSell && <Link to="/new">Sell</Link>}
        {user && <Link to="/dashboard">{dashLabel}</Link>}
        {user && <Link to="/messages">Messages</Link>}
        {user && <Link to="/notifications">🔔{unread ? `(${unread})` : ''}</Link>}
        {user && <Link to="/profile">Profile</Link>}
        {user?.role === 'admin' && <Link to="/admin">Admin</Link>}
        {!user && <Link to="/login">Login</Link>}
        {!user && <Link to="/signup" className="btn">Sign up</Link>}
        {user && <span className={`role-pill ${role}`}>{role}</span>}
        {user && <button onClick={async () => { await logout(); nav('/'); }}>Logout</button>}
      </div>
    </nav>
  );
}
