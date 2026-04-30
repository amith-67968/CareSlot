/**
 * CareSlot auth context.
 * Keeps React state in sync with persisted Supabase tokens.
 */

import { createContext, useContext, useEffect, useState } from 'react';
import {
  authAPI,
  clearStoredAuth,
  readStoredAuth,
  saveStoredAuth,
} from '../services/api';

const AuthContext = createContext(null);
const AUTH_CHANGED_EVENT = 'careslot_auth_changed';

function toUserData(data) {
  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: data.expires_at,
    expires_in: data.expires_in,
    user_id: data.user_id,
    email: data.email,
  };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => readStoredAuth());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const syncAuth = () => setUser(readStoredAuth());
    window.addEventListener('storage', syncAuth);
    window.addEventListener(AUTH_CHANGED_EVENT, syncAuth);
    return () => {
      window.removeEventListener('storage', syncAuth);
      window.removeEventListener(AUTH_CHANGED_EVENT, syncAuth);
    };
  }, []);

  const login = async (email, password, remember = true) => {
    setLoading(true);
    try {
      const data = await authAPI.login(email, password);
      const userData = saveStoredAuth(toUserData(data), remember);
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (email, password, fullName, extraProfile = {}) => {
    setLoading(true);
    try {
      const data = await authAPI.signup(email, password, fullName, extraProfile);

      if (!data.access_token) {
        return {
          needsConfirmation: true,
          message: data.message || 'Check your email to confirm your account',
          email,
        };
      }

      const userData = saveStoredAuth(toUserData(data), true);
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // Expired sessions are still cleared locally.
    }
    clearStoredAuth();
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
