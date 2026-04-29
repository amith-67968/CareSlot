/**
 * CareSlot — Auth Context
 * Manages authentication state across the app.
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('careslot_auth');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('careslot_auth');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const data = await authAPI.login(email, password);
    const userData = {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      user_id: data.user_id,
      email: data.email,
    };
    localStorage.setItem('careslot_auth', JSON.stringify(userData));
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
    localStorage.setItem('careslot_auth', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch {
      /* ignore */
    }
    localStorage.removeItem('careslot_auth');
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
