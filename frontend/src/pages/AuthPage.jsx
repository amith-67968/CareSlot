/**
 * CareSlot — Auth Page
 * Split-screen login/signup matching the provided design.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HeartPulse, Mail, Lock, Eye, EyeOff, User, ArrowRight, Loader2 } from 'lucide-react';

export default function AuthPage() {
  const [tab, setTab] = useState('login');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login, signup } = useAuth();

  /* Form fields */
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [remember, setRemember] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (tab === 'login') {
        await login(email, password);
      } else {
        if (password.length < 8) {
          setError('Password must be at least 8 characters');
          setLoading(false);
          return;
        }
        await signup(email, password, fullName);
      }
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* LEFT PANEL — Branding */}
      <div className="auth-left">
        <div className="auth-left-inner">
          <div className="auth-logo-card">
            <div className="auth-logo-icon-big">
              <HeartPulse size={64} strokeWidth={1.5} />
            </div>
            <span className="auth-logo-label">CARE SLOT</span>
          </div>
          <h2 className="auth-tagline">
            Precision Medicine.<br />Human Care.
          </h2>
          <p className="auth-tagline-sub">
            Empowering healthcare professionals with AI-driven insights to deliver exceptional patient outcomes.
          </p>
        </div>
      </div>

      {/* RIGHT PANEL — Form */}
      <div className="auth-right">
        <div className="auth-form-container">
          {/* Header icon */}
          <div className="auth-header-icon">
            <HeartPulse size={28} />
          </div>
          <h1 className="auth-form-title">
            {tab === 'login' ? 'Welcome Back' : 'Create Account'}
          </h1>
          <p className="auth-form-subtitle">
            {tab === 'login'
              ? 'Log in to access your secure dashboard.'
              : 'Sign up to start your health journey.'}
          </p>

          {/* Tab Toggle */}
          <div className="auth-tabs">
            <button
              type="button"
              className={`auth-tab ${tab === 'login' ? 'auth-tab-active' : ''}`}
              onClick={() => { setTab('login'); setError(''); }}
            >
              Login
            </button>
            <button
              type="button"
              className={`auth-tab ${tab === 'signup' ? 'auth-tab-active' : ''}`}
              onClick={() => { setTab('signup'); setError(''); }}
            >
              Sign Up
            </button>
          </div>

          {/* Error banner */}
          {error && <div className="auth-error">{error}</div>}

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form">
            {tab === 'signup' && (
              <div className="auth-field">
                <label htmlFor="auth-name">Full Name</label>
                <div className="auth-input-wrap">
                  <User size={16} className="auth-input-icon" />
                  <input
                    id="auth-name"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    minLength={2}
                  />
                </div>
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="auth-email">Email Address</label>
              <div className="auth-input-wrap">
                <Mail size={16} className="auth-input-icon" />
                <input
                  id="auth-email"
                  type="email"
                  placeholder="doctor@clinic.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="auth-pw">Password</label>
              <div className="auth-input-wrap">
                <Lock size={16} className="auth-input-icon" />
                <input
                  id="auth-pw"
                  type={showPw ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={tab === 'signup' ? 8 : 1}
                />
                <button
                  type="button"
                  className="auth-pw-toggle"
                  onClick={() => setShowPw(!showPw)}
                  aria-label="Toggle password visibility"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {tab === 'login' && (
              <div className="auth-row">
                <label className="auth-remember">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                  />
                  <span>Remember me</span>
                </label>
                <button type="button" className="auth-forgot-link">
                  Forgot password?
                </button>
              </div>
            )}

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <Loader2 size={18} className="auth-spinner" />
              ) : (
                <>
                  {tab === 'login' ? 'Login to Dashboard' : 'Create Account'}
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="auth-divider">
            <span>Secure Provider Access</span>
          </div>

          <p className="auth-switch-text">
            {tab === 'login' ? (
              <>
                New to CareSlot?{' '}
                <button type="button" onClick={() => { setTab('signup'); setError(''); }}>
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button type="button" onClick={() => { setTab('login'); setError(''); }}>
                  Log in
                </button>
              </>
            )}
          </p>

          <p className="auth-legal">
            By logging in, you agree to our <a href="#">Terms of Service</a> and{' '}
            <a href="#">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </div>
  );
}
