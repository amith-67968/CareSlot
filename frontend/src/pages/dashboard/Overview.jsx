/**
 * CareSlot — Dashboard Overview
 * Main dashboard page with health summary, quick actions, and activity feed.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { appointmentAPI, notificationAPI } from '../../services/api';
import {
  MessageCircle, ScanEye, ClipboardList, CalendarCheck,
  Activity, TrendingUp, Heart, Clock,
  ArrowRight, Bell, ChevronRight,
} from 'lucide-react';

const QUICK_ACTIONS = [
  {
    icon: MessageCircle, label: 'AI Chat', desc: 'Symptom analysis',
    to: '/dashboard/chat', color: '#3b82f6',
  },
  {
    icon: ScanEye, label: 'Skin Scan', desc: 'Image analysis',
    to: '/dashboard/skin', color: '#8b5cf6',
  },
  {
    icon: ClipboardList, label: 'PCOD Check', desc: 'Risk assessment',
    to: '/dashboard/pcod', color: '#ec4899',
  },
  {
    icon: CalendarCheck, label: 'Book Appt', desc: 'Schedule visit',
    to: '/dashboard/appointments', color: '#14b8a6',
  },
];

const STATS = [
  { icon: Heart, label: 'Health Score', value: '86%', trend: '+2%', color: '#ef4444' },
  { icon: Activity, label: 'Consultations', value: '12', trend: '+3', color: '#3b82f6' },
  { icon: TrendingUp, label: 'Assessments', value: '5', trend: '+1', color: '#8b5cf6' },
  { icon: Clock, label: 'Reminders', value: '3', trend: 'Active', color: '#f59e0b' },
];

export default function Overview() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    appointmentAPI.list('scheduled').then((d) => setAppointments(d.appointments?.slice(0, 3) || [])).catch(() => {});
    notificationAPI.list(5).then((d) => setNotifications(d.notifications?.slice(0, 4) || [])).catch(() => {});
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <div className="dash-overview">
      {/* Welcome */}
      <div className="dash-welcome">
        <div>
          <h1 className="dash-welcome-title">{greeting} 👋</h1>
          <p className="dash-welcome-sub">Here's your health snapshot for today.</p>
        </div>
        <button className="dash-welcome-btn" onClick={() => navigate('/dashboard/chat')}>
          <MessageCircle size={16} />
          Start AI Chat
        </button>
      </div>

      {/* Stat cards */}
      <div className="dash-stats-grid">
        {STATS.map((s) => (
          <div key={s.label} className="dash-stat-card">
            <div className="dash-stat-icon" style={{ background: `${s.color}18`, color: s.color }}>
              <s.icon size={20} />
            </div>
            <div className="dash-stat-info">
              <span className="dash-stat-value">{s.value}</span>
              <span className="dash-stat-label">{s.label}</span>
            </div>
            <span className="dash-stat-trend" style={{ color: s.color }}>{s.trend}</span>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <h2 className="dash-section-title">Quick Actions</h2>
      <div className="dash-quick-grid">
        {QUICK_ACTIONS.map((a) => (
          <button key={a.label} className="dash-quick-card" onClick={() => navigate(a.to)}>
            <div className="dash-quick-icon" style={{ background: `${a.color}14`, color: a.color }}>
              <a.icon size={22} />
            </div>
            <div className="dash-quick-text">
              <span className="dash-quick-label">{a.label}</span>
              <span className="dash-quick-desc">{a.desc}</span>
            </div>
            <ArrowRight size={16} className="dash-quick-arrow" />
          </button>
        ))}
      </div>

      {/* Two-column: Appointments + Activity */}
      <div className="dash-bottom-grid">
        <div className="dash-panel">
          <div className="dash-panel-header">
            <h3>Upcoming Appointments</h3>
            <button onClick={() => navigate('/dashboard/appointments')}>
              View All <ChevronRight size={14} />
            </button>
          </div>
          {appointments.length === 0 ? (
            <div className="dash-panel-empty">
              <CalendarCheck size={32} strokeWidth={1.2} />
              <p>No upcoming appointments</p>
              <button className="dash-panel-empty-btn" onClick={() => navigate('/dashboard/appointments')}>
                Book Now
              </button>
            </div>
          ) : (
            <div className="dash-appt-list">
              {appointments.map((a) => (
                <div key={a.id} className="dash-appt-item">
                  <div className="dash-appt-date">
                    <span>{new Date(a.appointment_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                    <small>{a.appointment_time}</small>
                  </div>
                  <div className="dash-appt-info">
                    <strong>{a.doctor_name}</strong>
                    <span>{a.hospital_name}</span>
                  </div>
                  <span className={`dash-appt-badge dash-appt-${a.status}`}>{a.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="dash-panel">
          <div className="dash-panel-header">
            <h3>Recent Notifications</h3>
            <button onClick={() => navigate('/dashboard/notifications')}>
              View All <ChevronRight size={14} />
            </button>
          </div>
          {notifications.length === 0 ? (
            <div className="dash-panel-empty">
              <Bell size={32} strokeWidth={1.2} />
              <p>You're all caught up!</p>
            </div>
          ) : (
            <div className="dash-notif-list">
              {notifications.map((n) => (
                <div key={n.id} className={`dash-notif-item ${n.is_read ? '' : 'dash-notif-unread'}`}>
                  <Bell size={16} />
                  <div>
                    <strong>{n.title}</strong>
                    <p>{n.body}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
