/**
 * CareSlot — Skin Analysis Upload Page (Premium Redesign)
 * AI-Powered Dermatology Assistant — upload + symptoms → redirect to results
 */

import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { skinAPI } from '../../services/api';
import {
  Upload, X, Loader2, Image as ImgIcon, Stethoscope, Clock,
  CheckCircle2, Brain, MapPin, FileImage, Activity,
  AlertTriangle, Thermometer, Zap, Flame, Hand, Droplets,
} from 'lucide-react';

const SYMPTOMS = [
  { key: 'itching', label: 'Itching', icon: Droplets },
  { key: 'redness', label: 'Redness', icon: AlertTriangle },
  { key: 'pain', label: 'Pain', icon: Zap },
  { key: 'burning_sensation', label: 'Burning', icon: Flame },
  { key: 'fever', label: 'Fever', icon: Thermometer },
  { key: 'swelling', label: 'Swelling', icon: Hand },
];

const BODY_PARTS = [
  '', 'Face', 'Scalp', 'Neck', 'Chest', 'Back', 'Abdomen',
  'Left Arm', 'Right Arm', 'Left Leg', 'Right Leg',
  'Hands', 'Feet', 'Groin', 'Other',
];

const LOADING_STEPS = [
  { label: 'Processing image...', icon: FileImage },
  { label: 'Running AI analysis...', icon: Brain },
  { label: 'Generating medical explanation...', icon: Stethoscope },
  { label: 'Preparing your report...', icon: Activity },
];

const SEV_STYLES = {
  mild: 'skin-sev-mild',
  moderate: 'skin-sev-moderate',
  severe: 'skin-sev-severe',
};

export default function SkinAnalysis() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [syms, setSyms] = useState({});
  const [bodyPart, setBodyPart] = useState('');
  const [duration, setDuration] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [showHist, setShowHist] = useState(false);
  const [toast, setToast] = useState(null);
  const dropRef = useRef(null);
  const fileRef = useRef(null);

  const showToast = useCallback((msg, type = 'error') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  const pickFile = useCallback((f) => {
    if (!f) return;
    if (!['image/jpeg', 'image/png', 'image/webp', 'image/jpg'].includes(f.type)) {
      showToast('Please upload JPEG, PNG, or WebP image');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      showToast('Image too large. Maximum size is 10 MB');
      return;
    }
    setError('');
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, [showToast]);

  const clearFile = () => {
    setFile(null);
    setPreview(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    dropRef.current?.classList.remove('skin-drop-active');
    pickFile(e.dataTransfer.files?.[0]);
  }, [pickFile]);

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setLoadingStep(0);
    setError('');

    // Simulate step progression
    const stepTimer = setInterval(() => {
      setLoadingStep((s) => (s < LOADING_STEPS.length - 1 ? s + 1 : s));
    }, 2000);

    try {
      const symptomsData = {
        ...syms,
        duration: duration || undefined,
        affected_body_part: bodyPart || undefined,
        additional_notes: notes || undefined,
      };
      const result = await skinAPI.analyze(file, symptomsData);
      clearInterval(stepTimer);

      // Navigate to results page with data
      navigate(`/dashboard/skin-results/${result.prediction_id || 'latest'}`, {
        state: { result, fromUpload: true },
      });
    } catch (e) {
      clearInterval(stepTimer);
      setLoading(false);
      setError(e.message || 'Analysis failed. Please try again.');
      showToast(e.message || 'Analysis failed', 'error');
    }
  };

  const loadHistory = async () => {
    try {
      const r = await skinAPI.getHistory();
      setHistory(r.predictions || []);
    } catch {
      setHistory([]);
    }
    setShowHist(true);
  };

  const toggleSym = (key) => {
    setSyms((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="skin-page">
      {/* Header */}
      <div className="skin-header">
        <div className="skin-header-left">
          <div className="skin-header-icon">
            <Stethoscope size={24} />
          </div>
          <div>
            <h1>AI Dermatology Assistant</h1>
            <p className="skin-header-sub">
              Upload a skin image for AI-powered preliminary assessment
            </p>
          </div>
        </div>
        <button className="skin-history-btn" onClick={loadHistory}>
          <Clock size={16} /> Past Scans
        </button>
      </div>

      {/* Main Grid */}
      <div className="skin-grid">
        {/* LEFT — Upload */}
        <div className="skin-upload-card">
          <h3><Upload size={18} /> Upload Skin Image</h3>

          <div
            ref={dropRef}
            className="skin-dropzone"
            onDrop={handleDrop}
            onDragOver={(e) => {
              e.preventDefault();
              dropRef.current?.classList.add('skin-drop-active');
            }}
            onDragLeave={() => dropRef.current?.classList.remove('skin-drop-active')}
            onClick={() => fileRef.current?.click()}
          >
            {preview ? (
              <div className="skin-preview-wrap">
                <img src={preview} alt="Preview" className="skin-preview-img" />
                <button
                  className="skin-preview-clear"
                  onClick={(e) => { e.stopPropagation(); clearFile(); }}
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <div>
                <div className="skin-drop-icon"><Upload size={26} /></div>
                <p className="skin-drop-title">Drag & drop image here</p>
                <p className="skin-drop-sub">or click to browse files</p>
                <div className="skin-formats">
                  <span className="skin-format-tag">JPG</span>
                  <span className="skin-format-tag">PNG</span>
                  <span className="skin-format-tag">WebP</span>
                  <span className="skin-format-tag">Max 10 MB</span>
                </div>
              </div>
            )}
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="skin-file-input"
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
          </div>

          {file && (
            <p className="skin-preview-name">
              <FileImage size={13} style={{ display: 'inline', verticalAlign: '-2px' }} />{' '}
              {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        {/* RIGHT — Symptoms */}
        <div className="skin-symptoms-card">
          <h3><Activity size={18} /> Symptoms & Details</h3>

          <div className="skin-symptom-grid">
            {SYMPTOMS.map((s) => (
              <label key={s.key} className="skin-check-label" title={s.label}>
                <div className="skin-checkbox-icon">
                  {syms[s.key] && <CheckCircle2 size={12} />}
                </div>
                <input
                  type="checkbox"
                  checked={!!syms[s.key]}
                  onChange={() => toggleSym(s.key)}
                />
                <span>{s.label}</span>
              </label>
            ))}
          </div>

          <div className="skin-field-group">
            <div>
              <label className="skin-field-label">Affected Body Part</label>
              <select
                className="skin-select"
                value={bodyPart}
                onChange={(e) => setBodyPart(e.target.value)}
              >
                <option value="">Select area (optional)</option>
                {BODY_PARTS.filter(Boolean).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="skin-field-label">Duration of Symptoms</label>
              <input
                type="text"
                className="skin-text-input"
                placeholder="e.g., 3 days, 2 weeks"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>

            <div>
              <label className="skin-field-label">Additional Notes</label>
              <textarea
                className="skin-notes-input"
                placeholder="Describe any other observations..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <button
            className="skin-analyze-btn"
            onClick={analyze}
            disabled={!file || loading}
          >
            {loading ? (
              <><Loader2 size={18} className="auth-spinner" /> Analyzing...</>
            ) : (
              <><Stethoscope size={18} /> Analyze Skin Condition</>
            )}
          </button>

          {error && <div className="skin-error">{error}</div>}
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="skin-loading-overlay">
          <div className="skin-loading-card">
            <h3>Analyzing Your Skin Image</h3>
            <div className="skin-loading-steps">
              {LOADING_STEPS.map((step, i) => {
                const StepIcon = step.icon;
                const isDone = i < loadingStep;
                const isActive = i === loadingStep;
                return (
                  <div
                    key={i}
                    className={`skin-loading-step ${isActive ? 'skin-loading-step-active' : ''} ${isDone ? 'skin-loading-step-done' : ''}`}
                  >
                    <div className="skin-loading-step-icon">
                      {isDone ? <CheckCircle2 size={14} /> : <StepIcon size={14} />}
                    </div>
                    {step.label}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHist && (
        <div className="skin-history-overlay" onClick={() => setShowHist(false)}>
          <div className="skin-history-modal" onClick={(e) => e.stopPropagation()}>
            <div className="skin-history-top">
              <h2>Past Skin Scans</h2>
              <button onClick={() => setShowHist(false)}><X size={18} /></button>
            </div>
            {history.length === 0 ? (
              <p className="skin-history-empty">No previous scans found.</p>
            ) : (
              <div className="skin-history-list">
                {history.map((h) => (
                  <div key={h.id} className="skin-history-item">
                    <div className="skin-history-item-info">
                      <strong>{h.predicted_condition}</strong>
                      <small>
                        {h.created_at
                          ? new Date(h.created_at).toLocaleDateString('en-US', {
                              year: 'numeric', month: 'short', day: 'numeric',
                            })
                          : ''}
                      </small>
                    </div>
                    <span
                      className={`skin-severity-badge ${SEV_STYLES[h.severity_level] || SEV_STYLES.mild}`}
                    >
                      {h.severity_level}
                    </span>
                    <button
                      className="skin-history-view-btn"
                      onClick={() => {
                        setShowHist(false);
                        navigate(`/dashboard/skin-results/${h.id}`);
                      }}
                    >
                      View Report
                    </button>
                  </div>
                ))}
              </div>
            )}
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
