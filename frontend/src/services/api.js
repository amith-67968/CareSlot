/**
 * CareSlot API service layer.
 * Centralizes backend requests, auth persistence, and token refresh.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const AUTH_KEY = 'careslot_auth';
const REMEMBER_KEY = 'careslot_remember';
const AUTH_CHANGED_EVENT = 'careslot_auth_changed';

let refreshPromise = null;

export function readStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY) || sessionStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    clearStoredAuth();
    return null;
  }
}

function resolveAuthStorage(remember) {
  if (remember === true) return localStorage;
  if (remember === false) return sessionStorage;
  if (localStorage.getItem(AUTH_KEY)) return localStorage;
  if (sessionStorage.getItem(AUTH_KEY)) return sessionStorage;
  return localStorage;
}

export function saveStoredAuth(auth, remember) {
  const storage = resolveAuthStorage(remember);
  const otherStorage = storage === localStorage ? sessionStorage : localStorage;
  const nextAuth = { ...(readStoredAuth() || {}), ...auth };

  storage.setItem(AUTH_KEY, JSON.stringify(nextAuth));
  otherStorage.removeItem(AUTH_KEY);
  localStorage.setItem(REMEMBER_KEY, storage === localStorage ? 'true' : 'false');
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  return nextAuth;
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(REMEMBER_KEY);
  sessionStorage.removeItem(AUTH_KEY);
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
}

function getToken() {
  return readStoredAuth()?.access_token || null;
}

function getRequestUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

async function fetchWithRedirect(path, options, headers) {
  let res;
  try {
    res = await fetch(getRequestUrl(path), { ...options, headers });
  } catch (err) {
    throw new Error('Cannot connect to server. Please check if the backend is running.', { cause: err });
  }

  if (res.status === 307 || res.status === 308) {
    const location = res.headers.get('location');
    if (location) return fetchWithRedirect(location, options, headers);
  }

  return res;
}

async function refreshAuth() {
  const currentAuth = readStoredAuth();
  if (!currentAuth?.refresh_token) return null;

  if (!refreshPromise) {
    refreshPromise = fetchWithRedirect(
      '/api/auth/refresh',
      {
        method: 'POST',
        body: JSON.stringify({ refresh_token: currentAuth.refresh_token }),
      },
      { 'Content-Type': 'application/json' },
    )
      .then(async (res) => {
        if (!res.ok) throw new Error('Session expired');
        const refreshed = await res.json();
        return saveStoredAuth({ ...currentAuth, ...refreshed });
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };

  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  let res = await fetchWithRedirect(path, options, headers);

  if (res.status === 401 && !path.startsWith('/api/auth')) {
    try {
      const refreshed = await refreshAuth();
      if (refreshed?.access_token) {
        res = await fetchWithRedirect(path, options, {
          ...headers,
          Authorization: `Bearer ${refreshed.access_token}`,
        });
      }
    } catch {
      // Fall through to the final 401 handler.
    }
  }

  if (res.status === 401 && !path.startsWith('/api/auth')) {
    clearStoredAuth();
    if (window.location.pathname !== '/auth') {
      window.location.href = '/auth';
    }
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  if (res.status === 204) return null;

  try {
    return await res.json();
  } catch {
    return null;
  }
}

const get = (path) => request(path);
const post = (path, body) =>
  request(path, {
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body),
  });
const put = (path, body) =>
  request(path, { method: 'PUT', body: body === undefined ? undefined : JSON.stringify(body) });
const del = (path) => request(path, { method: 'DELETE' });

export const authAPI = {
  login: (email, password) => post('/api/auth/login', { email, password }),
  signup: (email, password, full_name, extraProfile = {}) =>
    post('/api/auth/signup', { email, password, full_name, ...extraProfile }),
  refresh: (refreshToken) => post('/api/auth/refresh', { refresh_token: refreshToken }),
  logout: () => post('/api/auth/logout'),
  resetPassword: (email) => post('/api/auth/reset-password', { email }),
};

export const profileAPI = {
  get: () => get('/api/profile'),
  update: (data) => put('/api/profile', data),
  getMedicalHistory: () => get('/api/profile/medical-history'),
  addMedicalHistory: (data) => post('/api/profile/medical-history', data),
};

export const chatAPI = {
  analyzeSymptoms: (symptoms, additionalContext) =>
    post('/api/chat/symptom-analysis', {
      symptoms,
      additional_context: additionalContext,
    }),
  conversation: (message, sessionId, latitude, longitude) =>
    post('/api/chat/conversation', {
      message,
      session_id: sessionId,
      latitude: latitude || null,
      longitude: longitude || null,
    }),
  getHistory: (limit = 20) => get(`/api/chat/history?limit=${limit}`),
};

export const skinAPI = {
  analyze: (imageFile, symptoms = {}) => {
    const form = new FormData();
    form.append('image', imageFile);
    form.append('symptoms', JSON.stringify(symptoms));
    return post('/api/skin/analyze', form);
  },
  getHistory: () => get('/api/skin/history'),
  getPrediction: (id) => get(`/api/skin/predictions/${id}`),
};

export const pcodAPI = {
  assess: (questionnaire) => post('/api/pcod/assess', questionnaire),
  getHistory: () => get('/api/pcod/history'),
  getAssessment: (id) => get(`/api/pcod/assessments/${id}`),
};

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

export const notificationAPI = {
  list: (limit = 50) => get(`/api/notifications?limit=${limit}`),
  markRead: (id) => put(`/api/notifications/${id}/read`),
  createReminder: (data) => post('/api/notifications/reminders', data),
  listReminders: (status) =>
    get(`/api/notifications/reminders${status ? `?status=${status}` : ''}`),
  cancelReminder: (id) =>
    put(`/api/notifications/reminders/${id}/cancel`),
};
