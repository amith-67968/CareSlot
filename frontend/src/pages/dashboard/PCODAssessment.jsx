/**
 * CareSlot — PCOD/PCOS Premium Assessment Questionnaire
 * Multi-step form with loading overlay, history modal, redirect to results.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { pcodAPI } from '../../services/api';
import {
  Loader2, Clock, X, ArrowRight, ArrowLeft,
  HeartPulse, Dumbbell, Brain, Stethoscope,
  Check, Circle, CheckCircle2, XCircle,
} from 'lucide-react';

/* ── Step definitions ── */
const STEPS = [
  {
    title: 'Menstrual Health',
    subtitle: 'Tell us about your menstrual cycle',
    icon: HeartPulse,
    fields: [
      { key: 'irregular_periods', label: 'Do you experience irregular periods?', type: 'bool', req: true },
      { key: 'period_frequency', label: 'How often do you get periods?', type: 'select', options: ['monthly', 'every 2-3 months', 'rarely'] },
      { key: 'heavy_bleeding', label: 'Heavy menstrual bleeding?', type: 'bool' },
    ],
  },
  {
    title: 'Physical Symptoms',
    subtitle: 'Physical changes you\'ve noticed',
    icon: Dumbbell,
    fields: [
      { key: 'weight_gain', label: 'Unexplained weight gain?', type: 'bool', req: true },
      { key: 'acne', label: 'Persistent acne?', type: 'bool', req: true },
      { key: 'facial_hair_growth', label: 'Excessive facial hair?', type: 'bool', req: true },
      { key: 'hair_thinning', label: 'Hair thinning or loss?', type: 'bool', req: true },
      { key: 'skin_darkening', label: 'Dark patches on skin?', type: 'bool' },
    ],
  },
  {
    title: 'Systemic Symptoms',
    subtitle: 'General health and well-being',
    icon: Brain,
    fields: [
      { key: 'fatigue', label: 'Chronic fatigue?', type: 'bool', req: true },
      { key: 'mood_swings', label: 'Frequent mood swings?', type: 'bool', req: true },
      { key: 'pelvic_pain', label: 'Pelvic pain?', type: 'bool' },
      { key: 'sleep_issues', label: 'Sleep disturbances?', type: 'bool' },
    ],
  },
  {
    title: 'Medical History & Lifestyle',
    subtitle: 'Background health information',
    icon: Stethoscope,
    fields: [
      { key: 'insulin_resistance_history', label: 'History of insulin resistance?', type: 'bool' },
      { key: 'diabetes_family_history', label: 'Family history of diabetes?', type: 'bool' },
      { key: 'thyroid_issues', label: 'Known thyroid issues?', type: 'bool' },
      { key: 'pcos_family_history', label: 'Family history of PCOS/PCOD?', type: 'bool' },
      { key: 'exercise_frequency', label: 'Exercise frequency', type: 'select', options: ['daily', 'weekly', 'rarely'] },
      { key: 'stress_level', label: 'Stress level', type: 'select', options: ['low', 'moderate', 'high'] },
      { key: 'age', label: 'Your age', type: 'number' },
    ],
  },
];

const LOADING_STEPS = [
  'Evaluating symptoms...',
  'Running AI prediction...',
  'Generating health insights...',
  'Preparing your report...',
];

export default function PCODAssessment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    irregular_periods: false, weight_gain: false, acne: false,
    facial_hair_growth: false, hair_thinning: false,
    fatigue: false, mood_swings: false,
  });
  const [loading, setLoading] = useState(false);
  const [loadStep, setLoadStep] = useState(0);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [showHist, setShowHist] = useState(false);
  const [toast, setToast] = useState(null);

  const set = useCallback((k, v) => setForm(p => ({ ...p, [k]: v })), []);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const next = () => {
    if (step < STEPS.length - 1) setStep(s => s + 1);
  };
  const prev = () => {
    if (step > 0) setStep(s => s - 1);
  };

  const submit = async () => {
    setLoading(true);
    setError('');
    setLoadStep(0);

    const interval = setInterval(() => {
      setLoadStep(s => (s < LOADING_STEPS.length - 1 ? s + 1 : s));
    }, 700);

    try {
      const result = await pcodAPI.assess(form);
      clearInterval(interval);
      if (result.assessment_id) {
        navigate(`/dashboard/pcod-results/${result.assessment_id}`);
      } else {
        showToast('Assessment completed', 'success');
        navigate('/dashboard/pcod-results/latest', { state: { result } });
      }
    } catch (e) {
      clearInterval(interval);
      setError(e.message || 'Assessment failed. Please try again.');
      showToast('Assessment failed', 'error');
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const r = await pcodAPI.getHistory();
      setHistory(r.assessments || []);
    } catch {
      setHistory([]);
    }
    setShowHist(true);
  };

  const StepIcon = STEPS[step]?.icon || HeartPulse;

  return (
    <div className="pcod-page">
      {/* Header */}
      <div className="pcod-header">
        <div className="pcod-header-left">
          <div className="pcod-header-icon">
            <HeartPulse size={22} />
          </div>
          <div>
            <h1>AI Women's Health Assessment</h1>
            <p className="pcod-header-sub">PCOD / PCOS risk screening powered by AI</p>
          </div>
        </div>
        <button className="pcod-history-btn" onClick={loadHistory}>
          <Clock size={15} /> Past Assessments
        </button>
      </div>

      {/* Stepper */}
      <div className="pcod-stepper">
        {STEPS.map((s, i) => (
          <div
            key={i}
            className={`pcod-step-item ${i < step ? 'pcod-step-done' : ''} ${i === step ? 'pcod-step-active' : ''}`}
          >
            <div className="pcod-step-circle">
              {i < step ? <Check size={14} /> : i + 1}
            </div>
            <span className="pcod-step-label">{s.title}</span>
          </div>
        ))}
      </div>

      {/* Question Card */}
      <div className="pcod-question-card" key={step}>
        <h2><StepIcon size={18} /> {STEPS[step].title}</h2>
        <p className="pcod-step-subtitle">{STEPS[step].subtitle}</p>

        <div className="pcod-fields">
          {STEPS[step].fields.map(f => (
            <div key={f.key} className="pcod-field">
              <label className="pcod-field-label">
                {f.label}
                {f.req && <span className="pcod-field-req">*</span>}
              </label>

              {f.type === 'bool' ? (
                <div className="pcod-toggle-row">
                  <button
                    type="button"
                    className={`pcod-toggle-card ${form[f.key] === true ? 'pcod-toggle-yes' : ''}`}
                    onClick={() => set(f.key, true)}
                  >
                    <CheckCircle2 size={15} /> Yes
                  </button>
                  <button
                    type="button"
                    className={`pcod-toggle-card ${form[f.key] === false ? 'pcod-toggle-no' : ''}`}
                    onClick={() => set(f.key, false)}
                  >
                    <XCircle size={15} /> No
                  </button>
                </div>
              ) : f.type === 'select' ? (
                <select
                  value={form[f.key] || ''}
                  onChange={e => set(f.key, e.target.value)}
                  className="pcod-select"
                >
                  <option value="">Select...</option>
                  {f.options.map(o => (
                    <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="number"
                  value={form[f.key] || ''}
                  onChange={e => set(f.key, parseInt(e.target.value) || undefined)}
                  placeholder="Enter..."
                  className="pcod-number-input"
                />
              )}
            </div>
          ))}
        </div>

        {error && <div className="pcod-error">{error}</div>}

        <div className="pcod-nav">
          {step > 0 && (
            <button className="pcod-nav-btn pcod-nav-prev" onClick={prev}>
              <ArrowLeft size={16} /> Previous
            </button>
          )}
          <div style={{ flex: 1 }} />
          {step < STEPS.length - 1 ? (
            <button className="pcod-nav-btn pcod-nav-next" onClick={next}>
              Next <ArrowRight size={16} />
            </button>
          ) : (
            <button className="pcod-nav-btn pcod-nav-submit" onClick={submit} disabled={loading}>
              {loading ? (
                <><Loader2 size={16} className="auth-spinner" /> Assessing...</>
              ) : (
                <>Submit Assessment <ArrowRight size={16} /></>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="pcod-loading-overlay">
          <div className="pcod-loading-card">
            <h3>Analyzing Your Health Data</h3>
            <div className="pcod-loading-steps">
              {LOADING_STEPS.map((label, i) => (
                <div
                  key={i}
                  className={`pcod-loading-step ${
                    i === loadStep ? 'pcod-loading-step-active' : i < loadStep ? 'pcod-loading-step-done' : ''
                  }`}
                >
                  <div className="pcod-loading-step-icon">
                    {i < loadStep ? <Check size={12} /> : i === loadStep ? <Loader2 size={12} className="auth-spinner" /> : <Circle size={10} />}
                  </div>
                  {label}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHist && (
        <div className="pcod-hist-overlay" onClick={() => setShowHist(false)}>
          <div className="pcod-hist-modal" onClick={e => e.stopPropagation()}>
            <div className="pcod-hist-top">
              <h2>Assessment History</h2>
              <button onClick={() => setShowHist(false)}><X size={16} /></button>
            </div>
            {history.length === 0 ? (
              <p className="pcod-hist-empty">No previous assessments yet.</p>
            ) : (
              <div className="pcod-hist-list">
                {history.map(h => (
                  <div
                    key={h.id}
                    className="pcod-hist-item"
                    onClick={() => { setShowHist(false); navigate(`/dashboard/pcod-results/${h.id}`); }}
                  >
                    <div className="pcod-hist-info">
                      <strong>
                        Risk: {h.risk_level?.toUpperCase()}
                        <span
                          className={`pcod-risk-badge pcod-risk-${h.risk_level}`}
                          style={{ marginLeft: '.5rem' }}
                        >
                          {(h.risk_score * 100).toFixed(0)}%
                        </span>
                      </strong>
                      <small>{h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}</small>
                    </div>
                    <button className="pcod-hist-view-btn">View Report</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`pcod-toast pcod-toast-${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {toast.msg}
        </div>
      )}
    </div>
  );
}
