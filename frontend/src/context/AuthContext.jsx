import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi } from '../api';
import { getAccessToken, getStoredTokens, setStoredTokens } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      setStoredTokens(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (studentId, password) => {
    const tokens = await authApi.login({ student_id: studentId, password });
    setStoredTokens(tokens);
    const me = await authApi.me();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    const tokens = getStoredTokens();
    try {
      if (tokens?.refresh_token) {
        await authApi.logout(tokens.refresh_token);
      }
    } catch {
      /* ignore */
    }
    setStoredTokens(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout, reloadUser: loadUser, isAuthenticated: !!user }),
    [user, loading, login, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
