import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import { Nav } from './Nav';
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
      </AuthProvider>
    </BrowserRouter>
  );
}
