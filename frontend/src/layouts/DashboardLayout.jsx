/**
 * CareSlot — Dashboard Layout (Redesigned)
 * Clean clinical sidebar + topbar + content
 */

import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ProfilePopup from '../components/ProfilePopup';
import ChatPopup from '../components/ChatPopup';
import {
  LayoutDashboard, ScanEye, CalendarCheck, MapPin,
  LogOut, Menu, X, HeartPulse, ChevronRight,
  UserCircle, Settings, Search,
} from 'lucide-react';

const NAV = [
  { to: '/dashboard',              icon: LayoutDashboard, label: 'Dashboard',        end: true },
  { to: '/dashboard/detection',    icon: ScanEye,         label: 'Disease Detection' },
  { to: '/dashboard/appointments', icon: CalendarCheck,   label: 'Appointments' },
  { to: '/dashboard/hospitals',    icon: MapPin,           label: 'Hospital Site' },
];

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/auth');
  };

  const initial = (user?.email || 'U').charAt(0).toUpperCase();
  const userName = user?.full_name || user?.email?.split('@')[0] || 'User';

  return (
    <div className="dash-layout">
      {sidebarOpen && (
        <div className="dash-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`dash-sidebar ${sidebarOpen ? 'dash-sidebar-open' : ''}`}>
        {/* Brand */}
        <div className="dash-sidebar-top">
          <a href="/" className="dash-brand">
            <span className="dash-brand-icon">
              <HeartPulse size={20} strokeWidth={2.4} />
            </span>
            <span className="dash-brand-text">CareSlot AI</span>
          </a>
          <button
            className="dash-sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>



        {/* Navigation */}
        <nav className="dash-nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `dash-nav-link ${isActive ? 'dash-nav-active' : ''}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              <ChevronRight size={14} className="dash-nav-chevron" />
            </NavLink>
          ))}
        </nav>


      </aside>

      {/* Main */}
      <div className="dash-main">
        {/* Topbar */}
        <header className="dash-topbar">
          <button
            className="dash-menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={22} />
          </button>

          <div className="dash-search-bar">
            <Search size={16} />
            <input type="text" placeholder="Search patient ID or condition..." />
          </div>

          <div className="dash-topbar-right">
          </div>
        </header>

        {/* Content */}
        <main className="dash-content">
          <Outlet />
        </main>
      </div>

      {/* Floating Chat */}
      <ChatPopup />

      {/* Profile Popup */}
      {profileOpen && (
        <ProfilePopup onClose={() => setProfileOpen(false)} onLogout={handleLogout} />
      )}
    </div>
  );
}
