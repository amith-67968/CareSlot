/**
 * CareSlot — Profile Popup
 * Slide-out panel with user info, history tabs, and logout.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { profileAPI, appointmentAPI, chatAPI } from '../services/api';
import {
  X, User, Mail, Phone, Calendar, Droplets,
  CalendarCheck, MessageCircle, Edit3, Save, Loader2, LogOut,
} from 'lucide-react';

export default function ProfilePopup({ onClose, onLogout }) {
  const { user } = useAuth();
  const [tab, setTab] = useState('info');
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [appointments, setAppointments] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileData, apptData] = await Promise.allSettled([
        profileAPI.get(),
        appointmentAPI.list(),
      ]);

      if (profileData.status === 'fulfilled') {
        setProfile(profileData.value.profile || profileData.value);
        setForm(profileData.value.profile || profileData.value);
      }
      if (apptData.status === 'fulfilled') {
        setAppointments(apptData.value.appointments || []);
      }

      try {
        const chatData = await chatAPI.getHistory();
        const sessions = chatData.sessions || [];
        // Flatten sessions into displayable items (show first user message per session)
        const items = sessions.map((s) => {
          const firstUserMsg = s.messages?.find((m) => m.role === 'user');
          return {
            id: s.session_id,
            message: firstUserMsg?.message || 'Chat session',
            role: 'user',
            created_at: s.created_at || firstUserMsg?.created_at,
            messageCount: s.messages?.length || 0,
          };
        });
        setChatHistory(items);
      } catch { /* chat history optional */ }
    } catch (err) {
      console.error('Profile load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await profileAPI.update({
        full_name: form.full_name,
        phone: form.phone,
        date_of_birth: form.date_of_birth,
        gender: form.gender,
        blood_group: form.blood_group,
      });
      setProfile({ ...profile, ...form });
      setEditing(false);
    } catch (err) {
      console.error('Save error:', err);
    } finally {
      setSaving(false);
    }
  };

  const TABS = [
    { id: 'info', label: 'Personal Info', icon: User },
    { id: 'appointments', label: 'Appointments', icon: CalendarCheck },
    { id: 'chats', label: 'Chat History', icon: MessageCircle },
  ];

  return (
    <div className="pp-overlay" onClick={onClose}>
      <div className="pp-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="pp-header">
          <h2>My Profile</h2>
          <button className="pp-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* User banner */}
        <div className="pp-banner">
          <div className="pp-avatar-large">
            {(profile?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="pp-banner-info">
            <h3>{profile?.full_name || user?.email?.split('@')[0] || 'User'}</h3>
            <span>{user?.email}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="pp-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`pp-tab ${tab === t.id ? 'pp-tab-active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              <t.icon size={14} />
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="pp-content">
          {loading ? (
            <div className="pp-loading">
              <Loader2 size={24} className="pp-spinner" />
              <span>Loading...</span>
            </div>
          ) : (
            <>
              {/* Personal Info */}
              {tab === 'info' && (
                <div className="pp-info">
                  <div className="pp-info-header">
                    <h4>Personal Information</h4>
                    {!editing ? (
                      <button className="pp-edit-btn" onClick={() => setEditing(true)}>
                        <Edit3 size={14} /> Edit
                      </button>
                    ) : (
                      <button className="pp-save-btn" onClick={handleSave} disabled={saving}>
                        {saving ? <Loader2 size={14} className="pp-spinner" /> : <Save size={14} />}
                        Save
                      </button>
                    )}
                  </div>

                  <div className="pp-fields">
                    <ProfileField icon={User} label="Full Name" value={profile?.full_name}
                      editing={editing} onChange={(v) => setForm({ ...form, full_name: v })} formValue={form.full_name} />
                    <ProfileField icon={Mail} label="Email" value={profile?.email || user?.email} />
                    <ProfileField icon={Phone} label="Phone" value={profile?.phone}
                      editing={editing} onChange={(v) => setForm({ ...form, phone: v })} formValue={form.phone} />
                    <ProfileField icon={Calendar} label="Date of Birth" value={profile?.date_of_birth}
                      editing={editing} type="date" onChange={(v) => setForm({ ...form, date_of_birth: v })} formValue={form.date_of_birth} />
                    <ProfileField icon={User} label="Gender" value={profile?.gender}
                      editing={editing} type="select" options={['male', 'female', 'other']}
                      onChange={(v) => setForm({ ...form, gender: v })} formValue={form.gender} />
                    <ProfileField icon={Droplets} label="Blood Group" value={profile?.blood_group}
                      editing={editing} onChange={(v) => setForm({ ...form, blood_group: v })} formValue={form.blood_group} />
                  </div>
                </div>
              )}

              {/* Appointment History */}
              {tab === 'appointments' && (
                <div className="pp-history">
                  <h4>Appointment History ({appointments.length})</h4>
                  {appointments.length === 0 ? (
                    <div className="pp-empty">No appointments yet</div>
                  ) : (
                    <div className="pp-history-list">
                      {appointments.map((a) => (
                        <div key={a.id} className="pp-history-item">
                          <div className="pp-history-date">
                            {new Date(a.appointment_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </div>
                          <div className="pp-history-details">
                            <strong>{a.doctor_name}</strong>
                            <span>{a.doctor_specialty || 'General'}</span>
                            <span>{a.hospital_name}</span>
                          </div>
                          <span className={`pp-history-status pp-status-${a.status}`}>
                            {a.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Chat History */}
              {tab === 'chats' && (
                <div className="pp-history">
                  <h4>Chat Sessions ({chatHistory.length})</h4>
                  {chatHistory.length === 0 ? (
                    <div className="pp-empty">No chat history yet</div>
                  ) : (
                    <div className="pp-history-list">
                      {chatHistory.map((c, i) => (
                        <div key={c.id || i} className="pp-history-item">
                          <div className="pp-history-date">
                            {c.created_at
                              ? new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                              : '—'}
                          </div>
                          <div className="pp-history-details">
                            <strong>{c.message?.length > 50 ? c.message.slice(0, 50) + '...' : c.message || 'Chat session'}</strong>
                            <span>{c.messageCount || 0} messages</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Logout */}
        <div className="pp-footer">
          <button className="pp-logout" onClick={onLogout}>
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

function ProfileField({ icon: Icon, label, value, editing, type, options, onChange, formValue }) {
  if (editing && onChange) {
    if (type === 'select') {
      return (
        <div className="pp-field">
          <Icon size={16} className="pp-field-icon" />
          <div className="pp-field-body">
            <label>{label}</label>
            <select value={formValue || ''} onChange={(e) => onChange(e.target.value)}>
              <option value="">Select...</option>
              {options.map((o) => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
            </select>
          </div>
        </div>
      );
    }
    return (
      <div className="pp-field">
        <Icon size={16} className="pp-field-icon" />
        <div className="pp-field-body">
          <label>{label}</label>
          <input type={type || 'text'} value={formValue || ''} onChange={(e) => onChange(e.target.value)} />
        </div>
      </div>
    );
  }

  return (
    <div className="pp-field">
      <Icon size={16} className="pp-field-icon" />
      <div className="pp-field-body">
        <label>{label}</label>
        <span>{value || '—'}</span>
      </div>
    </div>
  );
}
