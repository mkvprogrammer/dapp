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
  const [amount, setAmount] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    const id = Number(auctionId);
    return Promise.all([auctionsApi.get(id), auctionsApi.leaderboard(id)])
      .then(([a, lb]) => {
        setAuction(a);
        setLeaderboard(lb.entries || []);
      })
      .finally(() => setLoading(false));
  }, [auctionId]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 15000);
    return () => clearInterval(timer);
  }, [load]);

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
          <span>Осталось: {formatTimeLeft(auction.end_time)}</span>
        </div>
      </header>

      {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}
      {message && <p style={{ color: 'var(--color-success)' }}>{message}</p>}

      <div className="AuctionDetailsPage__layout">
        <div>
          <section className="Card" style={{ marginBottom: 24 }}>
            <div className="Card__header">
              <h2 className="Card__title">Текущий рейтинг</h2>
              <span className="RankBadge">
                <span className="LiveDot" /> Обновляется каждые 15 с
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
                </label>
                <input
                  id="amount"
                  className="Input"
                  type="number"
                  step="0.01"
                  min="0"
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
    </>
  );
}
