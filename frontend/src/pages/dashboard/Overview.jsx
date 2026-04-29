/**
 * CareSlot — Dashboard Overview (Redesigned)
 * Clean clinical dashboard with appointments, detection, and AI chat.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { appointmentAPI } from '../../services/api';
import {
  CalendarCheck, ChevronRight, Clock, MapPin,
  User, Plus, History,
} from 'lucide-react';

export default function Overview() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    appointmentAPI.list()
      .then((d) => setAppointments(d.appointments || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';
  const userName = user?.full_name || user?.email?.split('@')[0] || 'there';

  // Get upcoming appointments (scheduled ones, sorted by date)
  const upcoming = appointments
    .filter(a => a.status === 'scheduled')
    .sort((a, b) => new Date(a.appointment_date) - new Date(b.appointment_date))
    .slice(0, 5);

  const nextAppt = upcoming[0];

  return (
    <div className="ov-page">
      {/* Welcome Header */}
      <div className="ov-header">
        <h1 className="ov-title">Overview</h1>
        <p className="ov-subtitle">
          {greeting}, <strong>{userName}</strong>. Here is your daily summary.
        </p>
      </div>

      {/* ─── APPOINTMENTS SECTION ─── */}
      <section className="ov-section">
        <div className="ov-section-header">
          <h2 className="ov-section-label">YOUR APPOINTMENTS</h2>
          <button className="ov-history-link" onClick={() => navigate('/dashboard/appointments')}>
            <History size={14} />
            HISTORY
          </button>
        </div>

        {/* Next appointment alert */}
        {nextAppt && (
          <div className="ov-appt-alert">
            <CalendarCheck size={18} />
            <span>
              Next appointment: <strong>{nextAppt.doctor_name}</strong> — {nextAppt.doctor_specialty || 'General'}
              {' · '}{new Date(nextAppt.appointment_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              {' at '}{nextAppt.appointment_time}
            </span>
          </div>
        )}

        {/* Appointment list */}
        <div className="ov-appt-list">
          {loading ? (
            <div className="ov-loading">Loading appointments...</div>
          ) : upcoming.length === 0 ? (
            <div className="ov-empty">
              <CalendarCheck size={28} strokeWidth={1.3} />
              <p>No upcoming appointments</p>
            </div>
          ) : (
            upcoming.map((a) => {
              const dt = new Date(a.appointment_date);
              const timeStr = a.appointment_time || '';
              const [h, m] = timeStr.split(':');
              const hour12 = h ? (parseInt(h) % 12 || 12) : '';
              const ampm = h ? (parseInt(h) >= 12 ? 'PM' : 'AM') : '';

              return (
                <div key={a.id} className="ov-appt-row">
                  <div className="ov-appt-time">
                    <span className="ov-appt-hour">{hour12}:{m || '00'}</span>
                    <span className="ov-appt-ampm">{ampm}</span>
                  </div>
                  <div className="ov-appt-divider" />
                  <div className="ov-appt-info">
                    <strong>{a.doctor_name}</strong>
                    <span>{a.doctor_specialty || 'General Consultation'}</span>
                  </div>
                  <ChevronRight size={16} className="ov-appt-arrow" />
                </div>
              );
            })
          )}
        </div>

        {/* Book Appointment button */}
        <button className="ov-book-btn" onClick={() => navigate('/dashboard/appointments')}>
          <Plus size={16} />
          Book Appointment
        </button>
      </section>

      {/* ─── HEALTH DETECTION ─── */}
      <section className="ov-section">
        <div className="ov-section-header">
          <h2 className="ov-section-label">HEALTH DETECTION</h2>
        </div>

        <div className="ov-detection-cards-row">
          {/* Skin Detection Card */}
          <button className="ov-detect-card" onClick={() => navigate('/dashboard/detection', { state: { tab: 'skin' } })}>
            <div className="ov-detect-icon ov-detect-skin">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
            </div>
            <div className="ov-detect-text">
              <strong>Skin Analysis</strong>
              <span>Upload image for AI detection</span>
            </div>
            <ChevronRight size={16} className="ov-detect-arrow" />
          </button>

          {/* PCOD/PCOS Card */}
          <button className="ov-detect-card" onClick={() => navigate('/dashboard/detection', { state: { tab: 'pcod' } })}>
            <div className="ov-detect-icon ov-detect-pcod">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 12l2 2 4-4"/>
                <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3"/>
                <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/>
                <path d="M21 5c0 1.66-4.03 3-9 3S3 6.66 3 5s4.03-3 9-3 9 1.34 9 3"/>
              </svg>
            </div>
            <div className="ov-detect-text">
              <strong>PCOS / PCOD Check</strong>
              <span>Risk assessment questionnaire</span>
            </div>
            <ChevronRight size={16} className="ov-detect-arrow" />
          </button>
        </div>

        {/* Quick Stats */}
        <div className="ov-detect-stats">
          <div className="ov-detect-stat">
            <span className="ov-detect-stat-val">MobileNetV2</span>
            <span className="ov-detect-stat-lbl">Skin Model</span>
          </div>
          <div className="ov-detect-stat">
            <span className="ov-detect-stat-val">7 Classes</span>
            <span className="ov-detect-stat-lbl">Conditions</span>
          </div>
          <div className="ov-detect-stat">
            <span className="ov-detect-stat-val">HAM10000</span>
            <span className="ov-detect-stat-lbl">Dataset</span>
          </div>
        </div>
      </section>
    </div>
  );
}

