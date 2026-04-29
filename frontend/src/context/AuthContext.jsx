/**
 * CareSlot — Auth Context
 * Manages authentication state across the app.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);
const AUTH_KEY = 'careslot_auth';
const REMEMBER_KEY = 'careslot_remember';

/**
 * Resolve which storage backend to use.
 * If "remember me" was checked, use localStorage (survives browser close).
 * Otherwise use sessionStorage (cleared on close).
 */
function getStorage() {
  return localStorage.getItem(REMEMBER_KEY) === 'true'
    ? localStorage
    : sessionStorage;
}

/** Read the persisted auth object, checking both storages. */
function readAuth() {
  const raw = localStorage.getItem(AUTH_KEY) || sessionStorage.getItem(AUTH_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(AUTH_KEY);
    sessionStorage.removeItem(AUTH_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUser(readAuth());
    setLoading(false);
  }, []);

  const login = async (email, password, remember = false) => {
    const data = await authAPI.login(email, password);
    const userData = {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      user_id: data.user_id,
      email: data.email,
    };

    // Persist remember preference
    if (remember) {
      localStorage.setItem(REMEMBER_KEY, 'true');
      localStorage.setItem(AUTH_KEY, JSON.stringify(userData));
    } else {
      localStorage.removeItem(REMEMBER_KEY);
      localStorage.removeItem(AUTH_KEY);
      sessionStorage.setItem(AUTH_KEY, JSON.stringify(userData));
    }

    setUser(userData);
    return userData;
  };

  const signup = async (email, password, fullName, extraProfile = {}) => {
    const data = await authAPI.signup(email, password, fullName, extraProfile);

    // If Supabase requires email confirmation, no token is returned
    if (!data.access_token) {
      return { needsConfirmation: true, message: data.message || 'Check your email to confirm your account', email };
    }

    const userData = {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      user_id: data.user_id,
      email: data.email,
    };
    // New signups always persist (user just created account)
    localStorage.setItem(REMEMBER_KEY, 'true');
    localStorage.setItem(AUTH_KEY, JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch {
      /* ignore */
    }
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(REMEMBER_KEY);
    sessionStorage.removeItem(AUTH_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
