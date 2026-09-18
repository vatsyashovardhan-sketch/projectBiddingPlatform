import { useEffect } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import { Nav } from './Nav';
import { initMotion } from './motion';
import { Browse } from './pages/Browse';
import { ListingDetail } from './pages/ListingDetail';
import { Login, Signup, Profile } from './pages/Auth';
import { Forgot, Reset, VerifyEmail } from './pages/Password';
import { NewListing } from './pages/NewListing';
import { EditListing } from './pages/EditListing';
import { Dashboard } from './pages/Dashboard';
import { Messages } from './pages/Messages';
import { Admin } from './pages/Admin';
import { Notifications } from './pages/Notifications';
import { SellerProfile } from './pages/SellerProfile';
import { Sellers } from './pages/Sellers';
import './styles.css';

export default function App() {
  useEffect(() => initMotion(), []);
  return (
    <BrowserRouter>
      <AuthProvider>
        <Nav />
        <main className="container">
          <Routes>
            <Route path="/" element={<Browse />} />
            <Route path="/l/:id" element={<ListingDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot" element={<Forgot />} />
            <Route path="/reset" element={<Reset />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/new" element={<NewListing />} />
            <Route path="/edit/:id" element={<EditListing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/messages" element={<Messages />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/u/:id" element={<SellerProfile />} />
            <Route path="/sellers" element={<Sellers />} />
          </Routes>
        </main>
        <footer className="footer">
          <div className="footer-inner">
            <div>
              <span className="kicker">Teal Trust</span>
              <span className="brand">ProjectBidding</span>
              <p>Buy and sell ready-made project code —<br />with bidding, escrow-style payouts, and reviews.</p>
            </div>
            <div>
              <span className="kicker">Marketplace</span>
              <p><a href="/">Browse projects</a><br /><a href="/sellers">Top sellers</a><br /><a href="/new">Sell a project</a></p>
            </div>
            <div>
              <span className="kicker">Account</span>
              <p><a href="/login">Login</a><br /><a href="/signup">Sign up</a><br /><a href="/dashboard">Dashboard</a></p>
            </div>
          </div>
          <p className="footer-copy">© 2026 ProjectBidding · Demo marketplace (mock payments until Stripe keys are set)</p>
        </footer>
      </AuthProvider>
    </BrowserRouter>
  );
}
