import { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; }
  });

  async function load() {
    if (!localStorage.getItem('access_token')) return;
    try {
      const me = await api('/users/me');
      setUser(me);
      localStorage.setItem('user', JSON.stringify(me));
    } catch { /* logged out */ }
  }
  useEffect(() => { load(); }, []);

  async function signup(email, password, name, role) {
    const data = await api('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, name, role }) });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
  }
  async function login(email, password) {
    const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
  }
  async function logout() {
    try {
      await api('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') }) });
    } catch {}
    localStorage.clear();
    setUser(null);
  }
  return <Ctx.Provider value={{ user, setUser, signup, login, logout }}>{children}</Ctx.Provider>;
}
