import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { notificationsApi } from '../api';
import { useAuth } from './AuthContext';

const NotificationsContext = createContext(null);

export function NotificationsProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setUnreadCount(0);
      return;
    }
    try {
      const data = await notificationsApi.list({ limit: 1 });
      setUnreadCount(data.unread_count ?? 0);
    } catch {
      setUnreadCount(0);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refresh();
  }, [refresh, location.pathname]);

  const markRead = useCallback(
    async (id) => {
      await notificationsApi.markRead(id);
      setUnreadCount((n) => Math.max(0, n - 1));
      await refresh();
    },
    [refresh],
  );

  const markAllRead = useCallback(async () => {
    const res = await notificationsApi.markAllRead();
    const updated = res?.updated_count ?? 0;
    if (updated > 0) {
      setUnreadCount(0);
    } else {
      await refresh();
    }
    return res;
  }, [refresh]);

  const value = useMemo(
    () => ({ unreadCount, refresh, markRead, markAllRead }),
    [unreadCount, refresh, markRead, markAllRead],
  );

  return <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>;
}

export function useNotifications() {
  const ctx = useContext(NotificationsContext);
  if (!ctx) throw new Error('useNotifications must be used within NotificationsProvider');
  return ctx;
}
