/**
 * CareSlot — Auth Page
 * Split-screen login/signup matching the provided design.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HeartPulse, Mail, Lock, Eye, EyeOff, User, ArrowRight, Loader2, Phone, Calendar, Droplets } from 'lucide-react';

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
  const [phone, setPhone] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [bloodGroup, setBloodGroup] = useState('');
  const [remember, setRemember] = useState(false);

  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      if (tab === 'login') {
        await login(email, password);
        navigate('/dashboard');
      } else {
        if (password.length < 8) {
          setError('Password must be at least 8 characters');
          setLoading(false);
          return;
        }
        const extraProfile = {};
        if (phone) extraProfile.phone = phone;
        if (dob) extraProfile.date_of_birth = dob;
        if (gender) extraProfile.gender = gender;
        if (bloodGroup) extraProfile.blood_group = bloodGroup;

        const result = await signup(email, password, fullName, extraProfile);
        if (result.needsConfirmation) {
          setSuccess(result.message);
          setTab('login');
        } else {
          navigate('/dashboard');
        }
      }
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
          {success && <div className="auth-success">{success}</div>}

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form">
            {tab === 'signup' && (
              <>
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

                <div className="auth-field">
                  <label htmlFor="auth-phone">Phone Number</label>
                  <div className="auth-input-wrap">
                    <Phone size={16} className="auth-input-icon" />
                    <input
                      id="auth-phone"
                      type="tel"
                      placeholder="+91 98765 43210"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>
                </div>

                <div className="auth-row-fields">
                  <div className="auth-field">
                    <label htmlFor="auth-dob">Date of Birth</label>
                    <div className="auth-input-wrap">
                      <Calendar size={16} className="auth-input-icon" />
                      <input
                        id="auth-dob"
                        type="date"
                        value={dob}
                        onChange={(e) => setDob(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="auth-field">
                    <label htmlFor="auth-gender">Gender</label>
                    <div className="auth-input-wrap">
                      <User size={16} className="auth-input-icon" />
                      <select
                        id="auth-gender"
                        value={gender}
                        onChange={(e) => setGender(e.target.value)}
                      >
                        <option value="">Select...</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="auth-field">
                  <label htmlFor="auth-blood">Blood Group</label>
                  <div className="auth-input-wrap">
                    <Droplets size={16} className="auth-input-icon" />
                    <select
                      id="auth-blood"
                      value={bloodGroup}
                      onChange={(e) => setBloodGroup(e.target.value)}
                    >
                      <option value="">Select...</option>
                      <option value="A+">A+</option>
                      <option value="A-">A-</option>
                      <option value="B+">B+</option>
                      <option value="B-">B-</option>
                      <option value="AB+">AB+</option>
                      <option value="AB-">AB-</option>
                      <option value="O+">O+</option>
                      <option value="O-">O-</option>
                    </select>
                  </div>
                </div>
              </>
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
