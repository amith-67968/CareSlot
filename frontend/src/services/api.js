/**
 * CareSlot — API Service Layer
 * Centralized fetch wrapper for all backend endpoints.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/* ── Helpers ─────────────────────────────────────────────────────── */

function getToken() {
  try {
    const auth = JSON.parse(localStorage.getItem('careslot_auth') || '{}');
    return auth.access_token || null;
  } catch {
    return null;
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };

  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers, redirect: 'manual' });

  // Handle 307/308 redirects manually to preserve Authorization header
  if (res.status === 307 || res.status === 308) {
    const location = res.headers.get('location');
    if (location) {
      res = await fetch(location, { ...options, headers, redirect: 'follow' });
    }
  }

  if (res.status === 401 && !path.startsWith('/api/auth')) {
    localStorage.removeItem('careslot_auth');
    window.location.href = '/auth';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  return res.json();
}

const get = (path) => request(path);
const post = (path, body) =>
  request(path, {
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body),
  });
const put = (path, body) =>
  request(path, { method: 'PUT', body: JSON.stringify(body) });
const del = (path) => request(path, { method: 'DELETE' });

/* ── Auth ────────────────────────────────────────────────────────── */

export const authAPI = {
  login: (email, password) => post('/api/auth/login', { email, password }),
  signup: (email, password, full_name) =>
    post('/api/auth/signup', { email, password, full_name }),
  logout: () => post('/api/auth/logout'),
  resetPassword: (email) => post('/api/auth/reset-password', { email }),
};

/* ── Profile ─────────────────────────────────────────────────────── */

export const profileAPI = {
  get: () => get('/api/profile'),
  update: (data) => put('/api/profile', data),
  getMedicalHistory: () => get('/api/profile/medical-history'),
  addMedicalHistory: (data) => post('/api/profile/medical-history', data),
};

/* ── Chat ────────────────────────────────────────────────────────── */

export const chatAPI = {
  analyzeSymptoms: (symptoms, additionalContext) =>
    post('/api/chat/symptom-analysis', {
      symptoms,
      additional_context: additionalContext,
    }),
  conversation: (message, sessionId) =>
    post('/api/chat/conversation', { message, session_id: sessionId }),
  getHistory: (limit = 20) => get(`/api/chat/history?limit=${limit}`),
};

/* ── Skin ────────────────────────────────────────────────────────── */

export const skinAPI = {
  analyze: (imageFile, symptoms = {}) => {
    const form = new FormData();
    form.append('image', imageFile);
    form.append('symptoms', JSON.stringify(symptoms));
    return post('/api/skin/analyze', form);
  },
  getHistory: () => get('/api/skin/history'),
};

/* ── PCOD ────────────────────────────────────────────────────────── */

export const pcodAPI = {
  assess: (questionnaire) => post('/api/pcod/assess', questionnaire),
  getHistory: () => get('/api/pcod/history'),
};

/* ── Appointments ────────────────────────────────────────────────── */

export const appointmentAPI = {
  list: (status) =>
    get(`/api/appointments${status ? `?status=${status}` : ''}`),
  get: (id) => get(`/api/appointments/${id}`),
  create: (data) => post('/api/appointments', data),
  update: (id, data) => put(`/api/appointments/${id}`, data),
  cancel: (id) => del(`/api/appointments/${id}`),
  getSlots: (date, doctorName, type) =>
    get(
      `/api/appointments/slots?date=${date}${doctorName ? `&doctor_name=${doctorName}` : ''}${type ? `&consultation_type=${type}` : ''}`
    ),
};

/* ── Doctors ─────────────────────────────────────────────────────── */

export const doctorAPI = {
  findNearby: (latitude, longitude, specialty, radius = 5000, keyword) =>
    post('/api/doctors/nearby', {
      latitude,
      longitude,
      specialty,
      radius,
      keyword,
    }),
  getDetails: (placeId) => get(`/api/doctors/place/${placeId}`),
  getSpecialties: () => get('/api/doctors/specialties'),
};

/* ── Notifications ───────────────────────────────────────────────── */

export const notificationAPI = {
  list: (limit = 50) => get(`/api/notifications?limit=${limit}`),
  markRead: (id) => put(`/api/notifications/${id}/read`),
  createReminder: (data) => post('/api/notifications/reminders', data),
  listReminders: (status) =>
    get(`/api/notifications/reminders${status ? `?status=${status}` : ''}`),
  cancelReminder: (id) =>
    put(`/api/notifications/reminders/${id}/cancel`),
};
