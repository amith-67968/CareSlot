/**
 * CareSlot — Skin Analysis Results Page
 * Premium medical-report style UI with doctor recommendations + booking.
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { skinAPI, doctorAPI, appointmentAPI } from '../../services/api';
import {
  ArrowLeft, Shield, AlertTriangle, CheckCircle2,
  MapPin, Star, ExternalLink, X, Loader2, Calendar, Clock,
  Activity, Pill, Footprints, Brain,
  Building2, CalendarCheck,
} from 'lucide-react';

const SEV = {
  mild: { cls: 'skin-sev-mild', label: 'Mild', icon: CheckCircle2 },
  moderate: { cls: 'skin-sev-moderate', label: 'Moderate', icon: AlertTriangle },
  severe: { cls: 'skin-sev-severe', label: 'Severe', icon: Shield },
};

const URG = {
  low: { cls: 'skinr-urgency-low', label: 'Low Urgency' },
  medium: { cls: 'skinr-urgency-medium', label: 'Medium Urgency' },
  high: { cls: 'skinr-urgency-high', label: 'High Urgency' },
};

export default function SkinResults() {
  const { predictionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [result, setResult] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!location.state?.result);
  const [error, setError] = useState('');

  // Doctors
  const [doctors, setDoctors] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [geoError, setGeoError] = useState('');

  // Booking
  const [booking, setBooking] = useState(null); // selected doctor
  const [bookDate, setBookDate] = useState('');
  const [bookSlot, setBookSlot] = useState('');
  const [bookType, setBookType] = useState('in-person');
  const [bookNotes, setBookNotes] = useState('');
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [bookSubmitting, setBookSubmitting] = useState(false);

  // Toast
  const [toast, setToast] = useState(null);
  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  // Fetch prediction if not passed via state
  useEffect(() => {
    if (result) return;
    if (!predictionId || predictionId === 'latest') {
      setError('No analysis data available. Please run a new scan.');
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const data = await skinAPI.getPrediction(predictionId);
        setResult(data);
      } catch (e) {
        setError(e.message || 'Failed to load report');
      } finally {
        setLoading(false);
      }
    })();
  }, [predictionId, result]);

  // Fetch nearby dermatologists
  useEffect(() => {
    if (!result) return;
    setDocsLoading(true);
    if (!navigator.geolocation) {
      setGeoError('Geolocation not supported');
      setDocsLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const res = await doctorAPI.findNearby(
            pos.coords.latitude, pos.coords.longitude, 'dermatologist', 5000
          );
          setDoctors(res.results || []);
        } catch {
          setGeoError('Could not fetch nearby doctors');
        } finally {
          setDocsLoading(false);
        }
      },
      () => {
        setGeoError('Location access denied. Enable location for doctor recommendations.');
        setDocsLoading(false);
      },
      { timeout: 10000 }
    );
  }, [result]);

  // Fetch slots when date changes
  useEffect(() => {
    if (!bookDate) return;
    setSlotsLoading(true);
    (async () => {
      try {
        const res = await appointmentAPI.getSlots(bookDate);
        setSlots(res.slots || []);
      } catch {
        setSlots([]);
      } finally {
        setSlotsLoading(false);
      }
    })();
  }, [bookDate]);

  const openBooking = (doc) => {
    setBooking(doc);
    setBookDate('');
    setBookSlot('');
    setBookType('in-person');
    setBookNotes(result ? `Skin condition: ${result.predicted_condition}` : '');
    setSlots([]);
  };

  const submitBooking = async () => {
    if (!booking || !bookDate || !bookSlot) return;
    setBookSubmitting(true);
    try {
      await appointmentAPI.create({
        doctor_name: booking.name,
        doctor_specialty: 'Dermatologist',
        hospital_name: booking.name,
        hospital_address: booking.address,
        hospital_place_id: booking.place_id,
        appointment_date: bookDate,
        appointment_time: bookSlot,
        consultation_type: bookType,
        notes: bookNotes,
      });
      showToast('Appointment booked successfully!', 'success');
      setBooking(null);
    } catch (e) {
      showToast(e.message || 'Booking failed', 'error');
    } finally {
      setBookSubmitting(false);
    }
  };

  const renderStars = (rating) => {
    if (!rating) return <span className="skinr-doctor-reviews">No rating</span>;
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <Star key={i} size={12} className={i <= Math.round(rating) ? 'skinr-star' : 'skinr-star-empty'} />
      );
    }
    return <>{stars}</>;
  };

  const sev = result ? (SEV[result.severity_level] || SEV.mild) : SEV.mild;
  const urg = result ? (URG[result.urgency_level] || URG.low) : URG.low;
  const todayStr = new Date().toISOString().split('T')[0];

  // Loading state
  if (loading) {
    return (
      <div className="skinr-page">
        <div className="skin-skeleton skin-skeleton-title" />
        <div className="skin-skeleton skin-skeleton-card" />
        <div className="skin-skeleton skin-skeleton-card" />
      </div>
    );
  }

  // Error state
  if (error || !result) {
    return (
      <div className="skinr-page">
        <button className="skinr-back-btn" onClick={() => navigate('/dashboard/detection')}>
          <ArrowLeft size={16} /> Back to Upload
        </button>
        <div className="skinr-doctors-empty">
          <AlertTriangle size={40} style={{ marginBottom: '.5rem', color: '#d97706' }} />
          <p>{error || 'No report data available.'}</p>
          <button className="skin-analyze-btn" style={{ maxWidth: 260, margin: '1rem auto 0' }}
            onClick={() => navigate('/dashboard/detection')}>
            Run New Analysis
          </button>
        </div>
      </div>
    );
  }

  const SevIcon = sev.icon;

  return (
    <div className="skinr-page">
      {/* Back */}
      <button className="skinr-back-btn" onClick={() => navigate('/dashboard/detection')}>
        <ArrowLeft size={16} /> New Analysis
      </button>

      {/* Report Header */}
      <div className="skinr-report-header">
        <div>
          <h1>Skin Analysis Report</h1>
          <p className="skinr-report-meta">
            {result.created_at
              ? new Date(result.created_at).toLocaleDateString('en-US', {
                  year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
                })
              : new Date().toLocaleDateString('en-US', {
                  year: 'numeric', month: 'long', day: 'numeric',
                })}
          </p>
          {result.prediction_id && (
            <span className="skinr-report-id">Report #{result.prediction_id?.slice(0, 8)}</span>
          )}
        </div>
      </div>

      {/* Diagnosis Card */}
      <div className="skinr-diagnosis">
        {result.image_url && (
          <div className="skinr-image-wrap">
            <img src={result.image_url} alt="Skin scan" />
          </div>
        )}
        <div className="skinr-diagnosis-info">
          <h2 className="skinr-condition-name">{result.predicted_condition}</h2>
          <div className="skinr-badges">
            <span className={`skin-severity-badge ${sev.cls}`}>
              <SevIcon size={12} /> {sev.label}
            </span>
            <span className={`skinr-urgency-badge ${urg.cls}`}>{urg.label}</span>
            {result.is_urgent && (
              <span className="skinr-urgency-badge skinr-urgency-high">
                ⚠ Urgent Consultation Needed
              </span>
            )}
          </div>
          <div className="skinr-confidence">
            <span className="skinr-confidence-label">AI Confidence</span>
            <div className="skinr-confidence-bar">
              <div
                className="skinr-confidence-fill"
                style={{ width: `${(result.confidence_score * 100).toFixed(0)}%` }}
              />
            </div>
            <span className="skinr-confidence-pct">
              {(result.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
          {result.symptoms_summary?.length > 0 && (
            <div className="skinr-symptoms-chips">
              {result.symptoms_summary.map((s, i) => (
                <span key={i} className="skinr-symptom-chip">{s}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Assessment + Causes */}
      <div className="skinr-cards-grid">
        {result.combined_assessment && (
          <div className="skinr-card skinr-card-full">
            <h3><Brain size={16} /> AI Assessment</h3>
            <p className="skinr-assessment-text">{result.combined_assessment}</p>
          </div>
        )}

        {result.possible_causes?.length > 0 && (
          <div className="skinr-card">
            <h3><Activity size={16} /> Possible Causes</h3>
            <ul className="skinr-list skinr-list-amber">
              {result.possible_causes.map((c, i) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        )}

        {result.precautions?.length > 0 && (
          <div className="skinr-card">
            <h3><Shield size={16} /> Precautions</h3>
            <ul className="skinr-list">
              {result.precautions.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </div>
        )}

        {result.home_remedies?.length > 0 && (
          <div className="skinr-card">
            <h3><Pill size={16} /> Home Remedies</h3>
            <ul className="skinr-list skinr-list-green">
              {result.home_remedies.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}

        {result.next_steps?.length > 0 && (
          <div className="skinr-card">
            <h3><Footprints size={16} /> Recommended Next Steps</h3>
            <ul className="skinr-list skinr-list-purple">
              {result.next_steps.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div className="skinr-disclaimer">
        <AlertTriangle size={16} />
        <span>{result.disclaimer}</span>
      </div>

      {/* Nearby Dermatologists */}
      <div className="skinr-doctors-section">
        <div className="skinr-doctors-header">
          <h2><MapPin size={18} /> Nearby Dermatologists</h2>
          {docsLoading && <span className="skinr-doctors-status">Searching...</span>}
        </div>

        {docsLoading ? (
          <div className="skinr-doctors-loading">
            <Loader2 size={20} className="auth-spinner" /> Finding nearby specialists...
          </div>
        ) : geoError ? (
          <div className="skinr-doctors-empty">{geoError}</div>
        ) : doctors.length === 0 ? (
          <div className="skinr-doctors-empty">No dermatologists found nearby. Try expanding your search.</div>
        ) : (
          <div className="skinr-doctors-grid">
            {doctors.slice(0, 6).map((doc) => (
              <div key={doc.place_id} className="skinr-doctor-card">
                <h4 className="skinr-doctor-name">{doc.name}</h4>
                <div className="skinr-doctor-rating">
                  <div className="skinr-doctor-stars">{renderStars(doc.rating)}</div>
                  {doc.rating && (
                    <span className="skinr-doctor-rating-num">{doc.rating}</span>
                  )}
                  {doc.total_ratings && (
                    <span className="skinr-doctor-reviews">({doc.total_ratings})</span>
                  )}
                </div>
                <div className="skinr-doctor-address">
                  <MapPin size={12} />
                  <span>{doc.address}</span>
                </div>
                <div className="skinr-doctor-status">
                  {doc.is_open_now === true && <span className="skinr-open">● Open now</span>}
                  {doc.is_open_now === false && <span className="skinr-closed">● Closed</span>}
                </div>
                <div className="skinr-doctor-actions">
                  <button className="skinr-book-btn" onClick={() => openBooking(doc)}>
                    <CalendarCheck size={14} /> Book Appointment
                  </button>
                  <a
                    className="skinr-map-link"
                    href={`https://www.google.com/maps/place/?q=place_id:${doc.place_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="View on Maps"
                  >
                    <ExternalLink size={14} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {booking && (
        <div className="skinr-booking-overlay" onClick={() => setBooking(null)}>
          <div className="skinr-booking-modal" onClick={(e) => e.stopPropagation()}>
            <div className="skinr-booking-header">
              <h2>Book Appointment</h2>
              <button className="skinr-booking-close" onClick={() => setBooking(null)}>
                <X size={16} />
              </button>
            </div>
            <div className="skinr-booking-body">
              <div className="skinr-booking-info">
                <div className="skinr-booking-info-icon"><Building2 size={18} /></div>
                <div>
                  <strong>{booking.name}</strong>
                  <span>{booking.address}</span>
                </div>
              </div>

              <div className="skinr-booking-row">
                <div className="skinr-booking-field">
                  <label><Calendar size={13} style={{ display: 'inline', verticalAlign: '-2px' }} /> Date</label>
                  <input type="date" min={todayStr} value={bookDate}
                    onChange={(e) => { setBookDate(e.target.value); setBookSlot(''); }} />
                </div>
                <div className="skinr-booking-field">
                  <label>Consultation Type</label>
                  <select value={bookType} onChange={(e) => setBookType(e.target.value)}>
                    <option value="in-person">In-Person</option>
                    <option value="video">Video Call</option>
                    <option value="phone">Phone</option>
                  </select>
                </div>
              </div>

              {bookDate && (
                <div className="skinr-booking-field">
                  <label><Clock size={13} style={{ display: 'inline', verticalAlign: '-2px' }} /> Select Time Slot</label>
                  {slotsLoading ? (
                    <p style={{ fontSize: '.8rem', color: '#64748b' }}>Loading slots...</p>
                  ) : (
                    <div className="skinr-slots-grid">
                      {slots.map((s) => {
                        const t = s.time.slice(0, 5);
                        const hr = parseInt(t);
                        const label = hr >= 12 ? `${hr === 12 ? 12 : hr - 12}:${t.slice(3)} PM` : `${hr}:${t.slice(3)} AM`;
                        return (
                          <button key={s.time}
                            className={`skinr-slot ${bookSlot === s.time ? 'skinr-slot-active' : ''} ${!s.available ? 'skinr-slot-unavail' : ''}`}
                            disabled={!s.available}
                            onClick={() => setBookSlot(s.time)}
                          >{label}</button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              <div className="skinr-booking-field">
                <label>Notes</label>
                <textarea rows={2} value={bookNotes}
                  onChange={(e) => setBookNotes(e.target.value)}
                  placeholder="Any additional notes..." />
              </div>

              <button className="skinr-booking-submit"
                disabled={!bookDate || !bookSlot || bookSubmitting}
                onClick={submitBooking}
              >
                {bookSubmitting ? (
                  <><Loader2 size={16} className="auth-spinner" /> Booking...</>
                ) : (
                  <><CalendarCheck size={16} /> Confirm Appointment</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`skin-toast skin-toast-${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {toast.msg}
        </div>
      )}
    </div>
  );
}
