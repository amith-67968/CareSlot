/**
 * CareSlot — Dashboard Layout
 * Sidebar + Topbar + Content Outlet
 */

import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, MessageCircle, ScanEye, ClipboardList,
  CalendarCheck, MapPin, UserCircle, Bell, LogOut,
  Menu, X, HeartPulse, ChevronRight,
} from 'lucide-react';

const NAV = [
  { to: '/dashboard',            icon: LayoutDashboard, label: 'Overview',       end: true },
  { to: '/dashboard/chat',       icon: MessageCircle,   label: 'AI Chat' },
  { to: '/dashboard/skin',       icon: ScanEye,         label: 'Skin Analysis' },
  { to: '/dashboard/pcod',       icon: ClipboardList,   label: 'PCOD Assessment' },
  { to: '/dashboard/appointments', icon: CalendarCheck,  label: 'Appointments' },
  { to: '/dashboard/doctors',    icon: MapPin,           label: 'Find Doctors' },
  { to: '/dashboard/notifications', icon: Bell,          label: 'Notifications' },
  { to: '/dashboard/profile',    icon: UserCircle,       label: 'Profile' },
];

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/auth');
  };

  return (
    <div className="dash-layout">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="dash-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`dash-sidebar ${sidebarOpen ? 'dash-sidebar-open' : ''}`}>
        <div className="dash-sidebar-top">
          <a href="/" className="dash-brand">
            <span className="dash-brand-icon">
              <HeartPulse size={20} strokeWidth={2.4} />
            </span>
            <span className="dash-brand-text">CareSlot</span>
          </a>
          <button
            className="dash-sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

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

        <div className="dash-sidebar-footer">
          <button className="dash-logout-btn" onClick={handleLogout}>
            <LogOut size={18} />
            <span>Log Out</span>
          </button>
        </div>
      </aside>

      {/* Main area */}
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

          <div className="dash-topbar-right">
            <button
              className="dash-notif-btn"
              onClick={() => navigate('/dashboard/notifications')}
              aria-label="Notifications"
            >
              <Bell size={18} />
              <span className="dash-notif-dot" />
            </button>
            <div
              className="dash-avatar"
              onClick={() => navigate('/dashboard/profile')}
              role="button"
              tabIndex={0}
            >
              {(user?.email || 'U').charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="dash-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
