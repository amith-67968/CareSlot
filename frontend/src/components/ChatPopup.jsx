/**
 * CareSlot — Floating Chat Popup
 * AI health assistant with structured output:
 *  - Disease prediction with risk level
 *  - Precautions & home remedies as bullet points
 *  - Nearby doctor suggestions via Google Maps API
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { chatAPI } from '../services/api';
import useSpeechRecognition from '../hooks/useSpeechRecognition';
import {
  MessageCircle, X, Send, RotateCcw,
  AlertTriangle, Loader2, HeartPulse,
  ShieldAlert, Stethoscope, Home, MapPin,
  Star, ChevronRight, Activity,
  Pill, Navigation, Mic, MicOff,
} from 'lucide-react';

/* ── Helpers ──────────────────────────────────────────────────────── */

function RiskBadge({ level }) {
  if (!level) return null;
  const config = {
    low:      { label: 'Low Risk',      cls: 'chat-risk-low' },
    medium:   { label: 'Medium Risk',   cls: 'chat-risk-medium' },
    high:     { label: 'High Risk',     cls: 'chat-risk-high' },
    critical: { label: 'Critical Risk', cls: 'chat-risk-critical' },
  };
  const c = config[level] || config.medium;
  return <span className={`chat-risk-badge ${c.cls}`}>{c.label}</span>;
}

function StarRating({ rating }) {
  if (!rating) return <span className="chat-doctor-no-rating">No ratings</span>;
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <span className="chat-doctor-rating">
      {[...Array(full)].map((_, i) => <Star key={i} size={11} className="chat-star-filled" />)}
      {half && <Star size={11} className="chat-star-half" />}
      <span className="chat-rating-num">{rating.toFixed(1)}</span>
    </span>
  );
}

function DoctorCard({ doc }) {
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(doc.name)}&query_place_id=${doc.place_id}`;
  return (
    <div className="chat-doctor-card">
      <div className="chat-doctor-info">
        <div className="chat-doctor-name">{doc.name}</div>
        <StarRating rating={doc.rating} />
        {doc.total_ratings && (
          <span className="chat-doctor-reviews">({doc.total_ratings} reviews)</span>
        )}
        <div className="chat-doctor-address">
          <MapPin size={10} />
          <span>{doc.address}</span>
        </div>
        {doc.is_open_now !== null && doc.is_open_now !== undefined && (
          <span className={`chat-doctor-status ${doc.is_open_now ? 'chat-open' : 'chat-closed'}`}>
            {doc.is_open_now ? '● Open Now' : '● Closed'}
          </span>
        )}
      </div>
      <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="chat-maps-link" title="View on Google Maps">
        <Navigation size={13} />
      </a>
    </div>
  );
}

function StructuredResponse({ data }) {
  return (
    <div className="chat-structured-response">
      {/* Summary */}
      <div className="chat-section chat-section-summary">
        <p>{data.response}</p>
      </div>

      {/* Prediction */}
      {data.prediction && (
        <div className="chat-section">
          <div className="chat-section-title">
            <Activity size={13} />
            <span>Predicted Condition</span>
            <RiskBadge level={data.risk_level} />
          </div>
          <p className="chat-prediction-text">{data.prediction}</p>
        </div>
      )}

      {/* Precautions */}
      {data.precautions?.length > 0 && (
        <div className="chat-section">
          <div className="chat-section-title">
            <ShieldAlert size={13} />
            <span>Precautions</span>
          </div>
          <ul className="chat-bullet-list">
            {data.precautions.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}

      {/* Home Remedies */}
      {data.home_remedies?.length > 0 && (
        <div className="chat-section">
          <div className="chat-section-title">
            <Home size={13} />
            <span>Home Remedies</span>
          </div>
          <ul className="chat-bullet-list chat-bullet-remedies">
            {data.home_remedies.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      {/* Next Steps */}
      {data.next_steps?.length > 0 && (
        <div className="chat-section">
          <div className="chat-section-title">
            <ChevronRight size={13} />
            <span>Next Steps</span>
          </div>
          <ul className="chat-bullet-list chat-bullet-steps">
            {data.next_steps.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      {/* Specialist */}
      {data.recommended_specialist && (
        <div className="chat-section chat-specialist-banner">
          <Stethoscope size={13} />
          <span>Recommended: <strong>{data.recommended_specialist}</strong></span>
        </div>
      )}

      {/* Nearby Doctors */}
      {data.nearby_doctors?.length > 0 && (
        <div className="chat-section">
          <div className="chat-section-title">
            <MapPin size={13} />
            <span>Nearby Doctors</span>
          </div>
          <div className="chat-doctors-list">
            {data.nearby_doctors.map((doc, i) => (
              <DoctorCard key={i} doc={doc} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────────────── */

export default function ChatPopup() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [userLocation, setUserLocation] = useState(null);
  const messagesEnd = useRef(null);
  const inputRef = useRef(null);
  const {
    clearError: clearVoiceError,
    error: voiceError,
    isListening: voiceListening,
    isSupported: voiceSupported,
    stopListening: stopVoiceInput,
    toggleListening: toggleVoiceInput,
  } = useSpeechRecognition({
    value: input,
    onChange: setInput,
    disabled: loading,
  });

  // Request geolocation on first open — with IP-based fallback
  useEffect(() => {
    if (!open || userLocation) return;

    const fetchIPLocation = async () => {
      try {
        const res = await fetch('https://ipapi.co/json/');
        const data = await res.json();
        if (data.latitude && data.longitude) {
          setUserLocation({ lat: data.latitude, lng: data.longitude });
        }
      } catch {
        // Last resort — will just skip doctor suggestions
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => fetchIPLocation(),
        { enableHighAccuracy: false, timeout: 5000 },
      );
    } else {
      fetchIPLocation();
    }
  }, [open, userLocation]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    stopVoiceInput();

    const userMsg = { role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await chatAPI.conversation(
        text,
        sessionId,
        userLocation?.lat,
        userLocation?.lng,
      );

      const botMsg = {
        role: 'assistant',
        text: data.response || data.message || 'I received your message.',
        structured: data.is_structured ? data : null,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Sorry, I encountered an error. Please try again.', error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, sessionId, stopVoiceInput, userLocation]);

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const reset = () => {
    stopVoiceInput();
    setMessages([]);
    setInput('');
    clearVoiceError();
  };

  return (
    <>
      {/* FAB Button */}
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Open AI Chat">
          <MessageCircle size={24} />
          <span className="chat-fab-pulse" />
        </button>
      )}

      {/* Chat Window */}
      {open && (
        <div className="chat-popup">
          {/* Header */}
          <div className="chat-popup-header">
            <div className="chat-popup-header-left">
              <div className="chat-popup-logo">
                <HeartPulse size={18} />
              </div>
              <div>
                <h3>CareSlot AI</h3>
                <span className="chat-popup-status">
                  <span className="chat-popup-dot" />
                  Health guidance ready
                </span>
              </div>
            </div>
            <div className="chat-popup-actions">
              <button onClick={reset} title="Reset chat" className="chat-popup-reset">
                <RotateCcw size={14} />
              </button>
              <button onClick={() => setOpen(false)} title="Close" className="chat-popup-close-btn">
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="chat-popup-disclaimer">
            <AlertTriangle size={12} />
            <span>AI guidance only — not a medical diagnosis</span>
          </div>

          {/* Location indicator */}
          {open && !userLocation && (
            <button
              className="chat-popup-location-hint"
              onClick={() => {
                if (navigator.geolocation) {
                  navigator.geolocation.getCurrentPosition(
                    (pos) => setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                    () => {},
                    { enableHighAccuracy: false, timeout: 5000 },
                  );
                }
              }}
            >
              <MapPin size={10} />
              <span>📍 Fetching your location for doctor suggestions...</span>
            </button>
          )}

          {/* Messages */}
          <div className="chat-popup-messages">
            {messages.length === 0 && (
              <div className="chat-popup-empty">
                <div className="chat-popup-empty-icon">
                  <HeartPulse size={28} />
                </div>
                <p>Hi! I'm your AI health assistant. Describe your symptoms and I'll help with:</p>
                <div className="chat-popup-features">
                  <span><Activity size={11} /> Disease prediction</span>
                  <span><ShieldAlert size={11} /> Precautions</span>
                  <span><Pill size={11} /> Home remedies</span>
                  <span><MapPin size={11} /> Nearby doctors</span>
                </div>
                <div className="chat-popup-suggestions">
                  {['I have a headache', 'What is PCOD?', 'Skin rash remedies'].map((s) => (
                    <button key={s} onClick={() => { setInput(s); }} className="chat-popup-chip">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-popup-msg ${msg.role === 'user' ? 'chat-popup-msg-user' : 'chat-popup-msg-bot'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="chat-popup-msg-avatar">
                    <HeartPulse size={13} />
                  </div>
                )}
                <div className={`chat-popup-msg-bubble ${msg.error ? 'chat-popup-msg-error' : ''}`}>
                  {msg.structured ? (
                    <StructuredResponse data={msg.structured} />
                  ) : (
                    msg.text
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="chat-popup-msg-avatar chat-popup-msg-avatar-user">U</div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-popup-msg chat-popup-msg-bot">
                <div className="chat-popup-msg-avatar">
                  <HeartPulse size={13} />
                </div>
                <div className="chat-popup-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Input */}
          <div className="chat-popup-composer">
            <div className="chat-popup-input">
              <input
                ref={inputRef}
                type="text"
                placeholder={voiceListening ? 'Listening...' : 'Describe your symptoms...'}
                value={input}
                onChange={(e) => {
                  clearVoiceError();
                  setInput(e.target.value);
                }}
                onKeyDown={handleKey}
                disabled={loading}
              />
              <button
                type="button"
                className={`chat-voice-btn ${voiceListening ? 'chat-voice-active' : ''}`}
                onClick={() => {
                  toggleVoiceInput();
                  inputRef.current?.focus();
                }}
                disabled={loading || !voiceSupported}
                title={voiceSupported ? (voiceListening ? 'Stop voice input' : 'Start voice input') : 'Voice input is not supported in this browser'}
                aria-label={voiceListening ? 'Stop voice input' : 'Start voice input'}
                aria-pressed={voiceListening}
              >
                {voiceListening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>
              <button
                className="chat-popup-send"
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                {loading ? <Loader2 size={16} className="chat-popup-spinner" /> : <Send size={16} />}
              </button>
            </div>
            {voiceError && (
              <div className="chat-voice-error" role="status">
                <AlertTriangle size={12} />
                <span>{voiceError}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
