import { useState, useEffect, useCallback } from 'react';
import { appointmentAPI } from '../../services/api';
import { CalendarCheck, Plus, X, Loader2, Clock, MapPin, Video, Phone } from 'lucide-react';

const TYPE_ICONS = { 'in-person': MapPin, video: Video, phone: Phone };
const STATUS_COLORS = { scheduled: '#3b82f6', completed: '#22c55e', cancelled: '#94a3b8', 'no-show': '#ef4444' };

export default function Appointments() {
  const [appts, setAppts] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    doctor_name: '', doctor_specialty: '', hospital_name: '', hospital_address: '',
    appointment_date: '', appointment_time: '', consultation_type: 'in-person', notes: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    try { const r = await appointmentAPI.list(filter || undefined); setAppts(r.appointments || []); }
    catch { setAppts([]); } finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('');
    try {
      await appointmentAPI.create(form);
      setShowForm(false);
      setForm({ doctor_name: '', doctor_specialty: '', hospital_name: '', hospital_address: '', appointment_date: '', appointment_time: '', consultation_type: 'in-person', notes: '' });
      load();
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  };

  const cancel = async (id) => {
    if (!confirm('Cancel this appointment?')) return;
    try { await appointmentAPI.cancel(id); load(); } catch { /* cancellation is non-blocking */ }
  };

  return (
    <div className="appt-page">
      <div className="appt-header">
        <div><h1>Appointments</h1><p>Manage your upcoming and past appointments</p></div>
        <button className="appt-new-btn" onClick={() => setShowForm(true)}><Plus size={16} /> Book Appointment</button>
      </div>

      <div className="appt-filters">
        {['', 'scheduled', 'completed', 'cancelled'].map(f => (
          <button key={f} className={`appt-filter-btn ${filter === f ? 'appt-filter-active' : ''}`} onClick={() => setFilter(f)}>
            {f || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="appt-loading"><Loader2 size={24} className="auth-spinner" /></div>
      ) : appts.length === 0 ? (
        <div className="appt-empty">
          <CalendarCheck size={48} strokeWidth={1} />
          <h3>No appointments found</h3>
          <p>Book your first appointment to get started.</p>
          <button className="appt-new-btn" onClick={() => setShowForm(true)}><Plus size={16} /> Book Now</button>
        </div>
      ) : (
        <div className="appt-list">
          {appts.map(a => {
            const TIcon = TYPE_ICONS[a.consultation_type] || MapPin;
            return (
              <div key={a.id} className="appt-card">
                <div className="appt-card-left">
                  <div className="appt-card-date">
                    <span className="appt-card-day">{new Date(a.appointment_date).toLocaleDateString('en-US', { day: 'numeric' })}</span>
                    <span className="appt-card-month">{new Date(a.appointment_date).toLocaleDateString('en-US', { month: 'short' })}</span>
                  </div>
                </div>
                <div className="appt-card-body">
                  <div className="appt-card-row1">
                    <strong>{a.doctor_name}</strong>
                    <span className="appt-status-badge" style={{ background: `${STATUS_COLORS[a.status] || '#94a3b8'}18`, color: STATUS_COLORS[a.status] || '#94a3b8' }}>{a.status}</span>
                  </div>
                  {a.doctor_specialty && <span className="appt-specialty">{a.doctor_specialty}</span>}
                  <div className="appt-card-details">
                    <span><MapPin size={13} /> {a.hospital_name}</span>
                    <span><Clock size={13} /> {a.appointment_time}</span>
                    <span><TIcon size={13} /> {a.consultation_type}</span>
                  </div>
                  {a.notes && <p className="appt-notes">{a.notes}</p>}
                </div>
                {a.status === 'scheduled' && (
                  <button className="appt-cancel-btn" onClick={() => cancel(a.id)} title="Cancel">
                    <X size={16} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {showForm && (
        <div className="skin-history-overlay" onClick={() => setShowForm(false)}>
          <div className="appt-modal" onClick={e => e.stopPropagation()}>
            <div className="skin-history-top"><h2>Book Appointment</h2><button onClick={() => setShowForm(false)}><X size={18} /></button></div>
            <form onSubmit={submit} className="appt-form">
              <div className="appt-form-grid">
                <div className="appt-form-field">
                  <label>Doctor Name *</label>
                  <input required value={form.doctor_name} onChange={e => set('doctor_name', e.target.value)} placeholder="Dr. Smith" />
                </div>
                <div className="appt-form-field">
                  <label>Specialty</label>
                  <input value={form.doctor_specialty} onChange={e => set('doctor_specialty', e.target.value)} placeholder="Cardiologist" />
                </div>
                <div className="appt-form-field">
                  <label>Hospital / Clinic *</label>
                  <input required value={form.hospital_name} onChange={e => set('hospital_name', e.target.value)} placeholder="City Hospital" />
                </div>
                <div className="appt-form-field">
                  <label>Address</label>
                  <input value={form.hospital_address} onChange={e => set('hospital_address', e.target.value)} placeholder="123 Health St" />
                </div>
                <div className="appt-form-field">
                  <label>Date *</label>
                  <input type="date" required value={form.appointment_date} onChange={e => set('appointment_date', e.target.value)} />
                </div>
                <div className="appt-form-field">
                  <label>Time *</label>
                  <input type="time" required value={form.appointment_time} onChange={e => set('appointment_time', e.target.value)} />
                </div>
                <div className="appt-form-field">
                  <label>Type</label>
                  <select value={form.consultation_type} onChange={e => set('consultation_type', e.target.value)}>
                    <option value="in-person">In-Person</option>
                    <option value="video">Video Call</option>
                    <option value="phone">Phone Call</option>
                  </select>
                </div>
              </div>
              <div className="appt-form-field appt-form-full">
                <label>Notes</label>
                <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2} placeholder="Any special requirements..." />
              </div>
              {error && <div className="skin-error">{error}</div>}
              <button type="submit" className="appt-submit-btn" disabled={saving}>
                {saving ? <><Loader2 size={16} className="auth-spinner" /> Booking...</> : 'Confirm Booking'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
