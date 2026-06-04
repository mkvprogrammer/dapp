import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { notificationsApi } from '../api';
import { useNotifications } from '../context/NotificationsContext';
import EmptyState from '../components/ui/EmptyState';
import LoadingBlock from '../components/ui/LoadingBlock';

export default function NotificationsPage() {
  const { unreadCount, markRead, markAllRead } = useNotifications();
  const [data, setData] = useState({ items: [], unread_count: 0 });
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(false);
  const autoMarkedRef = useRef(false);

  const load = useCallback(() => {
    setLoading(true);
    return notificationsApi
      .list({ limit: 50 })
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    autoMarkedRef.current = false;
    load();
  }, [load]);

  /* При открытии страницы помечаем все как прочитанные — сбрасывает красный бейдж в шапке */
  useEffect(() => {
    if (loading || autoMarkedRef.current) return;
    if (data.unread_count <= 0) return;

    autoMarkedRef.current = true;
    setMarking(true);
    markAllRead()
      .then(() =>
        setData((prev) => ({
          ...prev,
          unread_count: 0,
          items: prev.items.map((n) => ({ ...n, is_read: true })),
        })),
      )
      .finally(() => setMarking(false));
  }, [loading, data.unread_count, markAllRead]);

  const handleMarkAll = async () => {
    setMarking(true);
    try {
      await markAllRead();
      setData((prev) => ({
        ...prev,
        unread_count: 0,
        items: prev.items.map((n) => ({ ...n, is_read: true })),
      }));
    } finally {
      setMarking(false);
    }
  };

  const handleMarkOne = async (id) => {
    await markRead(id);
    setData((prev) => ({
      ...prev,
      unread_count: Math.max(0, prev.unread_count - 1),
      items: prev.items.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    }));
  };

  const displayUnread = marking ? 0 : Math.max(data.unread_count, unreadCount);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Уведомления</h1>
          <p className="PageHeader__subtitle">
            {loading
              ? 'Загрузка…'
              : displayUnread > 0
                ? `Непрочитанных: ${displayUnread}`
                : 'Все уведомления прочитаны'}
          </p>
        </div>
        <button
          type="button"
          className="Btn Btn--secondary"
          onClick={handleMarkAll}
          disabled={marking || (!displayUnread && data.items.every((n) => n.is_read))}
        >
          {marking ? 'Обновление…' : 'Отметить все прочитанными'}
        </button>
      </header>

      {loading && <LoadingBlock />}

      {!loading && data.items.length === 0 && (
        <EmptyState title="Уведомлений нет">Здесь появятся события по аукционам, переводам и проектам.</EmptyState>
      )}

      {!loading && data.items.length > 0 && (
        <div className="NotificationsPage__list">
          {data.items.map((n) => (
            <article
              key={n.id}
              className={`NotificationCard Card${n.is_read ? '' : ' NotificationCard--unread'}`}
            >
              <div className="NotificationCard__head">
                <h3 className="NotificationCard__title">{n.title}</h3>
                {!n.is_read && (
                  <button
                    type="button"
                    className="Btn Btn--ghost Btn--sm NotificationCard__read-btn"
                    onClick={() => handleMarkOne(n.id)}
                  >
                    Прочитано
                  </button>
                )}
              </div>
              <p className="NotificationCard__body">{n.body}</p>
              <time className="NotificationCard__time">{new Date(n.created_at).toLocaleString('ru-RU')}</time>
              {n.meta?.auction_id && (
                <Link to={`/auctions/${n.meta.auction_id}`} className="NotificationCard__link Card__link">
                  Открыть аукцион →
                </Link>
              )}
              {n.meta?.project_id && !n.meta?.auction_id && (
                <Link to={`/projects/${n.meta.project_id}`} className="NotificationCard__link Card__link">
                  Открыть проект →
                </Link>
              )}
            </article>
          ))}
        </div>
      )}
    </>
  );
}
