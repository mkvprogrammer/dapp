import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { auctionsApi } from '../api';
import { ApiError } from '../api/client';
import PasswordInput from '../components/PasswordInput';
import { useAuth } from '../context/AuthContext';
import { formatDateTime, formatTimeLeft, formatTkn, getInitials } from '../utils/format';

export default function AuctionDetailsPage() {
  const { auctionId } = useParams();
  const { user } = useAuth();
  const [auction, setAuction] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [bidHistory, setBidHistory] = useState([]);
  const [amount, setAmount] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const loadLeaderboard = useCallback(() => {
    const id = Number(auctionId);
    return auctionsApi.leaderboard(id).then((lb) => setLeaderboard(lb.entries || []));
  }, [auctionId]);

  const load = useCallback(() => {
    const id = Number(auctionId);
    return Promise.all([
      auctionsApi.get(id),
      auctionsApi.leaderboard(id),
      auctionsApi.bidHistory(id).catch(() => ({ entries: [] })),
    ])
      .then(([a, lb, hist]) => {
        setAuction(a);
        setLeaderboard(lb.entries || []);
        setBidHistory(hist.entries || []);
      })
      .finally(() => setLoading(false));
  }, [auctionId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!auction || auction.status !== 'open') return undefined;
    const timer = setInterval(loadLeaderboard, 5000);
    return () => clearInterval(timer);
  }, [auction?.status, loadLeaderboard]);

  const myEntry = leaderboard.find((e) => e.student_id === user?.student_id);
  const myRank = myEntry ? leaderboard.indexOf(myEntry) + 1 : null;

  const handleBid = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await auctionsApi.bid(Number(auctionId), { amount: Number(amount), password });
      setMessage('Ставка принята');
      setAmount('');
      setPassword('');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка ставки');
    }
  };

  const handleCancel = async () => {
    setError('');
    setMessage('');
    if (!password) {
      setError('Введите пароль для отмены ставки');
      return;
    }
    try {
      await auctionsApi.cancelBid(Number(auctionId), { password });
      setMessage('Ставка отменена');
      setPassword('');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка отмены');
    }
  };

  if (loading) return <p>Загрузка…</p>;
  if (!auction) return <p>Аукцион не найден</p>;

  return (
    <>
      <p style={{ margin: '0 0 16px', fontSize: '0.875rem' }}>
        <Link to="/auctions">← Все аукционы</Link> · <Link to={`/projects/${auction.project_id}`}>Проект #{auction.project_id}</Link>
      </p>

      <header className="AuctionDetailsPage__banner">
        <span className="AuctionDetailsPage__banner-live">
          <span className="LiveDot" /> {auction.status}
        </span>
        <h1 className="AuctionDetailsPage__banner-title">{auction.resource_name}</h1>
        <div className="AuctionDetailsPage__banner-meta">
          <span>Начало: {formatDateTime(auction.start_time)}</span>
          <span>Окончание: {formatDateTime(auction.end_time)}</span>
          <span>Занятие: {formatDateTime(auction.lesson_start_time)}</span>
          <span>Мест: {auction.resource_limit}</span>
          {auction.location && <span>Место: {auction.location}</span>}
          {auction.resource_type && <span>Тип: {auction.resource_type}</span>}
          {auction.min_bid != null && <span>Мин. ставка: {formatTkn(auction.min_bid)}</span>}
          <span>Осталось: {formatTimeLeft(auction.end_time)}</span>
        </div>
        {auction.description && (
          <p className="AuctionDetailsPage__banner-desc" style={{ marginTop: 12, opacity: 0.9 }}>
            {auction.description}
          </p>
        )}
        {auction.image_url && (
          <img
            src={auction.image_url.startsWith('http') ? auction.image_url : auction.image_url}
            alt=""
            style={{ marginTop: 16, maxWidth: '100%', borderRadius: 12, maxHeight: 200, objectFit: 'cover' }}
          />
        )}
      </header>

      {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}
      {message && <p style={{ color: 'var(--color-success)' }}>{message}</p>}

      <div className="AuctionDetailsPage__layout">
        <div>
          <section className="Card" style={{ marginBottom: 24 }}>
            <div className="Card__header">
              <h2 className="Card__title">Текущий рейтинг</h2>
              <span className="RankBadge">
                <span className="LiveDot" /> {auction.status === 'open' ? 'Обновляется каждые 5 с' : 'Итоговый рейтинг'}
              </span>
            </div>
            <div className="Card__body Card__body--flush-top">
              <div className="TableWrap">
                <table className="Table">
                  <thead>
                    <tr>
                      <th>Место</th>
                      <th>Участник</th>
                      <th>Ставка</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.map((entry, i) => (
                      <tr
                        key={entry.wallet_address}
                        className={entry.student_id === user?.student_id ? 'AuctionDetailsPage__rank-row--you' : ''}
                      >
                        <td>
                          <span className="RankBadge">{i + 1}</span>
                        </td>
                        <td>
                          <span className="Avatar Avatar--sm" style={{ display: 'inline-flex', marginRight: 8 }}>
                            {getInitials(entry.full_name)}
                          </span>
                          {entry.full_name}
                          {entry.student_id === user?.student_id ? ' (вы)' : ''}
                          {entry.is_guaranteed ? ' ✓' : ''}
                        </td>
                        <td>
                          <strong>{formatTkn(entry.amount)}</strong>
                        </td>
                      </tr>
                    ))}
                    {leaderboard.length === 0 && (
                      <tr>
                        <td colSpan={3}>Пока нет ставок</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {bidHistory.length > 0 && (
            <section className="Card" style={{ marginTop: 24 }}>
              <div className="Card__header">
                <h2 className="Card__title">История ставок</h2>
              </div>
              <div className="Card__body Card__body--flush-top">
                <div className="TableWrap">
                  <table className="Table">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>Участник</th>
                        <th>Сумма</th>
                        <th>Действие</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bidHistory.map((ev) => (
                        <tr key={ev.id}>
                          <td>{formatDateTime(ev.created_at)}</td>
                          <td>{ev.full_name || ev.student_id}</td>
                          <td>{formatTkn(ev.amount)}</td>
                          <td>{ev.action}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          )}
        </div>

        <aside className="AuctionDetailsPage__bid Card">
          <h2 className="Card__title">Ваша ставка</h2>
          {myEntry ? (
            <p>
              Текущая ставка: <strong>{formatTkn(myEntry.amount)}</strong>
              {myRank && ` · Место #${myRank}`}
            </p>
          ) : (
            <p>Вы ещё не участвуете</p>
          )}

          {user?.role === 'student' && (
            <form onSubmit={handleBid} style={{ marginTop: 16 }}>
              <div className="Field Field--full">
                <label className="Field__label" htmlFor="amount">
                  Новая ставка (TKN)
                  {auction.min_bid != null && (
                    <span style={{ fontWeight: 400, color: 'var(--color-text-muted)' }}>
                      {' '}
                      · мин. {formatTkn(auction.min_bid)}
                    </span>
                  )}
                </label>
                <input
                  id="amount"
                  className="Input"
                  type="number"
                  step="0.01"
                  min={auction.min_bid ?? 0}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                />
              </div>
              <div className="Field Field--full">
                <label className="Field__label">Пароль аккаунта</label>
                <PasswordInput
                  id="bid-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="Btn Btn--primary Btn--block" style={{ marginTop: 12 }}>
                Повысить ставку
              </button>
              {myEntry && (
                <button type="button" className="Btn Btn--secondary Btn--block" style={{ marginTop: 8 }} onClick={handleCancel}>
                  Отозвать ставку
                </button>
              )}
            </form>
          )}
          {user?.role !== 'student' && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
              Ставки доступны только студентам (роль student).
            </p>
          )}
        </aside>
      </div>

      {(user?.role === 'organizer' || user?.role === 'admin') && (
        <OrganizerAttendancePanel auctionId={Number(auctionId)} />
      )}
    </>
  );
}

const ATTENDANCE_LABELS = {
  pending: 'Ожидает',
  present: 'Присутствовал',
  absent: 'Прогул',
  penalized: 'Штраф',
  no_bid: '—',
};

function OrganizerAttendancePanel({ auctionId }) {
  const [entries, setEntries] = useState([]);
  const [password, setPassword] = useState('');
  const [selectedStudent, setSelectedStudent] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    return auctionsApi.attendance(auctionId).then((data) => {
      setEntries(data.entries || []);
      if (!selectedStudent && data.entries?.length) {
        const first = data.entries.find((e) => e.attendance_label === 'pending');
        if (first) setSelectedStudent(first.student_id);
      }
    });
  }, [auctionId, selectedStudent]);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const runAction = async (fn) => {
    setError('');
    setMessage('');
    if (!password) {
      setError('Введите пароль кошелька организатора');
      return;
    }
    if (!selectedStudent) {
      setError('Выберите студента');
      return;
    }
    try {
      const res = await fn();
      setMessage(res.message || 'Готово');
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка');
    }
  };

  if (loading) return null;

  return (
    <section className="Card" style={{ marginTop: 24 }}>
      <div className="Card__header">
        <h2 className="Card__title">Посещаемость (преподаватель)</h2>
      </div>
      <div className="Card__body">
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: 16 }}>
          Подтвердите присутствие или отметьте прогул. Коды подтверждения не используются.
        </p>
        {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}
        {message && <p style={{ color: 'var(--color-success)' }}>{message}</p>}

        <div className="TableWrap">
          <table className="Table">
            <thead>
              <tr>
                <th>Студент</th>
                <th>Ставка</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.user_id}>
                  <td>
                    {e.full_name} ({e.student_id})
                  </td>
                  <td>{formatTkn(e.bid_amount)}</td>
                  <td>{ATTENDANCE_LABELS[e.attendance_label] || e.attendance_label}</td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={3}>Нет ставок для отметки посещения</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: 16, display: 'grid', gap: 12, maxWidth: 400 }}>
          <div className="Field Field--full">
            <label className="Field__label">Студент</label>
            <select
              className="Input"
              value={selectedStudent}
              onChange={(e) => setSelectedStudent(e.target.value)}
            >
              <option value="">—</option>
              {entries
                .filter((e) => e.attendance_label === 'pending')
                .map((e) => (
                  <option key={e.student_id} value={e.student_id}>
                    {e.student_id} — {e.full_name}
                  </option>
                ))}
            </select>
          </div>
          <div className="Field Field--full">
            <label className="Field__label">Пароль кошелька</label>
            <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button
              type="button"
              className="Btn Btn--primary"
              onClick={() =>
                runAction(() =>
                  auctionsApi.confirmAttendance(auctionId, {
                    student_id: selectedStudent,
                    password,
                  }),
                )
              }
            >
              Подтвердить присутствие
            </button>
            <button
              type="button"
              className="Btn Btn--secondary"
              onClick={() =>
                runAction(() =>
                  auctionsApi.markAbsent(auctionId, {
                    student_id: selectedStudent,
                    password,
                  }),
                )
              }
            >
              Отметить прогул
            </button>
            <button
              type="button"
              className="Btn Btn--secondary"
              onClick={() => runAction(() => auctionsApi.closeDay(auctionId, { password }))}
            >
              Закрыть день
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
