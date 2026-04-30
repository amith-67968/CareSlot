/**
 * CareSlot — PCOD/PCOS Results Page
 * Dedicated medical report with AI assessment, doctor recommendations, booking.
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { pcodAPI, doctorAPI, appointmentAPI } from '../../services/api';
import {
  ArrowLeft, AlertTriangle, CheckCircle2, ShieldAlert,
  Stethoscope, MapPin, Star, Clock, Calendar, X,
  HeartPulse, Sparkles, ShieldCheck, Apple, Dumbbell,
  Activity, Baby, Loader2, BookOpen, ExternalLink,
} from 'lucide-react';

const RISK_META = {
  low:    { bg: '#dcfce7', color: '#16a34a', Icon: CheckCircle2, label: 'Low Risk' },
  medium: { bg: '#fef3c7', color: '#b45309', Icon: AlertTriangle, label: 'Moderate Risk' },
  high:   { bg: '#fee2e2', color: '#dc2626', Icon: ShieldAlert,  label: 'High Risk' },
};

const FALLBACK_SLOTS = ['10:00', '11:00', '14:00', '15:00', '16:00'];

function getSpecialtyKey(specialist) {
  const label = (specialist || '').toLowerCase();
  if (label.includes('endocrin')) return 'endocrinologist';
  return 'gynecologist';
}

function getSpecialtyLabel(specialist) {
  return specialist || 'Gynecologist';
}

function formatSlotLabel(slot) {
  const value = typeof slot === 'string' ? slot : slot?.time;
  if (!value) return '';
  const [hourRaw, minute = '00'] = value.split(':');
  const hour = Number(hourRaw);
  if (Number.isNaN(hour)) return value;
  const hour12 = hour % 12 || 12;
  const suffix = hour >= 12 ? 'PM' : 'AM';
  return `${hour12}:${minute} ${suffix}`;
}

export default function PCODResults() {
  const { assessmentId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [report, setReport] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!report);
  const [doctors, setDoctors] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [bookingDoc, setBookingDoc] = useState(null);
  const [bookDate, setBookDate] = useState('');
  const [bookSlot, setBookSlot] = useState('');
  const [slots, setSlots] = useState([]);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [doctorNotice, setDoctorNotice] = useState('');

  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  /* Load report */
  useEffect(() => {
    if (report) { setLoading(false); return; }
    if (assessmentId === 'latest') { navigate('/dashboard/detection', { state: { tab: 'pcod' } }); return; }

    (async () => {
      try {
        const r = await pcodAPI.getAssessment(assessmentId);
        setReport(r);
      } catch {
        showToast('Failed to load report', 'error');
      } finally { setLoading(false); }
    })();
  }, [assessmentId, navigate, report, showToast]);

  /* Find nearby doctors */
  const findDoctors = useCallback(async () => {
    setLoadingDocs(true);
    setDoctorNotice('');
    try {
      if (!navigator.geolocation) {
        setDoctorNotice('Geolocation is not available in this browser.');
        return;
      }
      const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, { timeout: 8000 }));
      const specialty = getSpecialtyKey(report?.recommended_specialist);
      const keyword = 'PCOD PCOS women health gynecologist endocrinologist';
      const r = await doctorAPI.findNearby(pos.coords.latitude, pos.coords.longitude, specialty, 10000, keyword);
      const matches = r.results || r.doctors || [];
      setDoctors(matches);
      if (matches.length === 0) {
        setDoctorNotice('No nearby specialists were found. Try the Doctors page with a wider radius.');
      }
    } catch (e) {
      setDoctors([]);
      setDoctorNotice(e?.message || 'Location access denied. Enable location for doctor recommendations.');
    }
    finally { setLoadingDocs(false); }
  }, [report]);

  useEffect(() => { if (report) findDoctors(); }, [report, findDoctors]);

  /* Booking */
  const openBooking = (doc) => {
    setBookingDoc(doc);
    setBookDate('');
    setBookSlot('');
    setSlots([]);
  };

  const loadSlots = async (date) => {
    setBookDate(date);
    try {
      const r = await appointmentAPI.getSlots(date, bookingDoc?.name);
      setSlots(r.slots?.length ? r.slots : (r.available_slots?.length ? r.available_slots : FALLBACK_SLOTS));
    } catch {
      setSlots(FALLBACK_SLOTS);
    }
  };

  const confirmBooking = async () => {
    if (!bookDate || !bookSlot) return;
    setBookingLoading(true);
    try {
      await appointmentAPI.create({
        doctor_name: bookingDoc?.name || 'Specialist',
        doctor_specialty: getSpecialtyLabel(report?.recommended_specialist),
        hospital_name: bookingDoc?.name || 'Clinic',
        hospital_address: bookingDoc?.address || '',
        hospital_place_id: bookingDoc?.place_id,
        appointment_date: bookDate,
        appointment_time: bookSlot,
        consultation_type: 'in-person',
        notes: 'PCOD/PCOS assessment follow-up',
      });
      showToast('Appointment booked successfully!');
      setBookingDoc(null);
    } catch { showToast('Booking failed', 'error'); }
    finally { setBookingLoading(false); }
  };

  if (loading) return (
    <div className="pcodr-page" style={{ alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
      <Loader2 size={32} className="auth-spinner" style={{ color: '#a855f7' }} />
      <p style={{ color: '#64748b', marginTop: '.75rem' }}>Loading report...</p>
    </div>
  );

  if (!report) return (
    <div className="pcodr-page" style={{ alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
      <p style={{ color: '#64748b' }}>Report not found.</p>
      <button className="pcodr-back-btn" onClick={() => navigate('/dashboard/detection', { state: { tab: 'pcod' } })}>
        <ArrowLeft size={15} /> Back to Assessment
      </button>
    </div>
  );

  const risk = RISK_META[report.risk_level] || RISK_META.low;
  const scorePercent = ((report.risk_score || 0) * 100).toFixed(1);
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (circumference * (report.risk_score || 0));
  const dateStr = report.created_at ? new Date(report.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="pcodr-page">
      <button className="pcodr-back-btn" onClick={() => navigate('/dashboard/detection', { state: { tab: 'pcod' } })}>
        <ArrowLeft size={15} /> ← New Assessment
      </button>

      {/* Report Header */}
      <div className="pcodr-report-header">
        <div>
          <h1>PCOD / PCOS Risk Report</h1>
          <p className="pcodr-report-meta">{dateStr}</p>
          <p className="pcodr-report-id">Report: #{(report.assessment_id || report.id || '').slice(0, 8)}</p>
        </div>
        <HeartPulse size={40} style={{ opacity: .4 }} />
      </div>

      {/* Risk Score Card */}
      <div className="pcodr-risk-card">
        <div className="pcodr-score-ring">
          <svg viewBox="0 0 100 100">
            <circle className="pcodr-score-bg" cx="50" cy="50" r="42" />
            <circle
              className="pcodr-score-fill"
              cx="50" cy="50" r="42"
              stroke={risk.color}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <span className="pcodr-score-value">{scorePercent}%</span>
          <span className="pcodr-score-label">Risk</span>
        </div>

        <div className="pcodr-risk-info">
          <h2>Assessment Result</h2>
          <div className="pcodr-badges">
            <span className={`pcodr-urgency-badge pcodr-urgency-${report.risk_level}`}>
              <risk.Icon size={13} /> {risk.label}
            </span>
            {report.urgency_level && (
              <span className={`pcodr-urgency-badge pcodr-urgency-${report.urgency_level}`}>
                {report.urgency_level.toUpperCase()} Urgency
              </span>
            )}
            {report.is_urgent && (
              <span className="pcodr-urgency-badge pcodr-urgency-high">
                <AlertTriangle size={12} /> Urgent Consultation Needed
              </span>
            )}
          </div>

          {report.conditions_flagged?.length > 0 && (
            <div className="pcodr-condition-chips">
              {report.conditions_flagged.map((c, i) => (
                <span key={i} className="pcodr-condition-chip">{c}</span>
              ))}
            </div>
          )}

          {report.key_indicators?.length > 0 && (
            <div className="pcodr-indicator-chips">
              {report.key_indicators.map((k, i) => (
                <span key={i} className="pcodr-indicator-chip">{k}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* AI Assessment */}
      {report.combined_assessment && (
        <div className="pcodr-card pcodr-card-full">
          <h3><Sparkles size={16} /> AI Assessment</h3>
          <p className="pcodr-assessment-text">{report.combined_assessment}</p>
        </div>
      )}

      {/* Cards Grid */}
      <div className="pcodr-cards-grid">
        {report.possible_causes?.length > 0 && (
          <div className="pcodr-card">
            <h3><Activity size={16} /> Possible Causes</h3>
            <ul className="pcodr-list pcodr-list-pink">
              {report.possible_causes.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        )}

        {report.precautions?.length > 0 && (
          <div className="pcodr-card">
            <h3><ShieldCheck size={16} /> Precautions</h3>
            <ul className="pcodr-list pcodr-list-amber">
              {report.precautions.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </div>
        )}

        {report.recommendations?.length > 0 && (
          <div className="pcodr-card">
            <h3><BookOpen size={16} /> Medical Recommendations</h3>
            <ul className="pcodr-list">
              {report.recommendations.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}

        {report.lifestyle_recommendations?.length > 0 && (
          <div className="pcodr-card">
            <h3><HeartPulse size={16} /> Lifestyle Changes</h3>
            <ul className="pcodr-list pcodr-list-green">
              {report.lifestyle_recommendations.map((l, i) => <li key={i}>{l}</li>)}
            </ul>
          </div>
        )}

        {report.dietary_suggestions?.length > 0 && (
          <div className="pcodr-card">
            <h3><Apple size={16} /> Dietary Suggestions</h3>
            <ul className="pcodr-list pcodr-list-green">
              {report.dietary_suggestions.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </div>
        )}

        {report.exercise_recommendations?.length > 0 && (
          <div className="pcodr-card">
            <h3><Dumbbell size={16} /> Exercise Plan</h3>
            <ul className="pcodr-list pcodr-list-blue">
              {report.exercise_recommendations.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        )}

        {report.hormonal_insights && (
          <div className="pcodr-card">
            <h3><Activity size={16} /> Hormonal Insights</h3>
            <p className="pcodr-insight-text">{report.hormonal_insights}</p>
          </div>
        )}

        {report.fertility_note && report.fertility_note !== 'Not applicable' && (
          <div className="pcodr-card">
            <h3><Baby size={16} /> Fertility Note</h3>
            <p className="pcodr-insight-text">{report.fertility_note}</p>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="pcodr-disclaimer">
        <AlertTriangle size={16} />
        <span>{report.disclaimer || 'This is a risk assessment tool only, NOT a diagnosis. Please consult a specialist.'}</span>
      </div>

      {/* Doctors Section */}
      <div className="pcodr-doctors-section">
        <div className="pcodr-doctors-header">
          <h2><Stethoscope size={18} /> Recommended Specialists Near You</h2>
        </div>

        {loadingDocs ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
            <Loader2 size={24} className="auth-spinner" style={{ color: '#a855f7' }} />
            <p style={{ marginTop: '.5rem', fontSize: '.82rem' }}>Finding specialists...</p>
          </div>
        ) : doctors.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: '.82rem', padding: '2rem' }}>
            <p>{doctorNotice || 'Enable location to see nearby specialists.'}</p>
            <button
              className="skinr-book-btn"
              style={{ margin: '1rem auto 0', maxWidth: 180 }}
              onClick={findDoctors}
            >
              <MapPin size={14} /> Use My Location
            </button>
          </div>
        ) : (
          <div className="skinr-doctors-grid">
            {doctors.slice(0, 6).map((doc, i) => (
              <div key={doc.place_id || i} className="skinr-doctor-card">
                <div className="skinr-doctor-top">
                  <div className="skinr-doctor-avatar">
                    <Stethoscope size={18} />
                  </div>
                  <div className="skinr-doctor-info">
                    <h4>{doc.name}</h4>
                    <p className="skinr-doctor-specialty">{getSpecialtyLabel(report?.recommended_specialist)}</p>
                  </div>
                </div>
                <div className="skinr-doctor-meta">
                  {doc.rating && (
                    <span className="skinr-doctor-rating">
                      <Star size={12} /> {doc.rating}
                    </span>
                  )}
                  {doc.is_open_now !== undefined && (
                    <span className={`skinr-doctor-status ${doc.is_open_now ? 'skinr-open' : 'skinr-closed'}`}>
                      {doc.is_open_now ? 'Open' : 'Closed'}
                    </span>
                  )}
                </div>
                {doc.address && (
                  <p className="skinr-doctor-address"><MapPin size={12} /> {doc.address}</p>
                )}
                <div className="skinr-doctor-actions">
                  <button className="skinr-book-btn" onClick={() => openBooking(doc)}>
                    <Calendar size={14} /> Book Appointment
                  </button>
                  {doc.place_id && (
                    <a
                      className="skinr-map-link"
                      href={`https://www.google.com/maps/place/?q=place_id:${doc.place_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="View on Maps"
                    >
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {bookingDoc && (
        <div className="skinr-booking-overlay" onClick={() => setBookingDoc(null)}>
          <div className="skinr-booking-modal" onClick={e => e.stopPropagation()}>
            <div className="skinr-booking-header">
              <h3>Book Appointment</h3>
              <button onClick={() => setBookingDoc(null)}><X size={16} /></button>
            </div>
            <div className="skinr-booking-body">
              <p className="skinr-booking-doc"><Stethoscope size={14} /> {bookingDoc.name}</p>
              <label className="skinr-booking-label">Select Date</label>
              <input
                type="date"
                className="skinr-booking-date"
                value={bookDate}
                min={new Date().toISOString().split('T')[0]}
                onChange={e => loadSlots(e.target.value)}
              />
              {slots.length > 0 && (
                <>
                  <label className="skinr-booking-label">Available Slots</label>
                  <div className="skinr-slots-grid">
                    {slots.map((s, i) => {
                      const value = typeof s === 'string' ? s : s?.time;
                      const available = typeof s === 'string' ? true : s?.available !== false;
                      return (
                        <button
                          key={value || i}
                          className={`skinr-slot-btn ${bookSlot === value ? 'skinr-slot-active' : ''} ${!available ? 'skinr-slot-unavail' : ''}`}
                          disabled={!available}
                          onClick={() => setBookSlot(value)}
                        >
                          <Clock size={12} /> {formatSlotLabel(s)}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}
              <button
                className="skinr-confirm-btn"
                disabled={!bookDate || !bookSlot || bookingLoading}
                onClick={confirmBooking}
              >
                {bookingLoading ? <><Loader2 size={14} className="auth-spinner" /> Booking...</> : 'Confirm Appointment'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`pcod-toast pcod-toast-${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {toast.msg}
        </div>
      )}
    </div>
  );
}
