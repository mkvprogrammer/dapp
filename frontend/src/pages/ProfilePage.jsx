import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { usersApi } from '../api';
import { ApiError } from '../api/client';
import Alert from '../components/ui/Alert';
import EmptyState from '../components/ui/EmptyState';
import { useAuth } from '../context/AuthContext';
import { formatTkn, getInitials, roleLabel } from '../utils/format';

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [balances, setBalances] = useState(null);
  const [activity, setActivity] = useState([]);
  const [editName, setEditName] = useState('');
  const [editFaculty, setEditFaculty] = useState('');
  const [editMsg, setEditMsg] = useState('');
  const [editError, setEditError] = useState('');

  const reload = () => {
    usersApi.profile().then((p) => {
      setProfile(p);
      setEditName(p.full_name || '');
      setEditFaculty(p.faculty || '');
    });
    usersApi.balances().then(setBalances);
    usersApi.activity(15, 0).then((r) => setActivity(r.items || []));
  };

  useEffect(() => {
    reload();
  }, []);

  const saveProfile = async (e) => {
    e.preventDefault();
    setEditMsg('');
    setEditError('');
    try {
      await usersApi.updateProfile({
        full_name: editName.trim() || undefined,
        faculty: editFaculty.trim() || null,
      });
      setEditMsg('Профиль сохранён');
      reload();
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : 'Ошибка сохранения');
    }
  };

  return (
    <>
      <header className="PageHeader">
        <h1 className="PageHeader__title">Личный кабинет</h1>
        <p className="PageHeader__subtitle">Профиль, баланс и активность на платформе.</p>
      </header>

      <div className="Card PageSection">
        <div className="Card__body ProfileHero">
          <span className="Avatar Avatar--lg">{getInitials(user?.full_name)}</span>
          <div className="ProfileHero__info">
            <h2 className="ProfileHero__name">{user?.full_name}</h2>
            <p className="ProfileHero__meta">
              {roleLabel(user?.role)} · ITMO ID: {user?.student_id}
            </p>
            <p className="ProfileHero__wallet">Кошелёк: {user?.wallet_address}</p>
          </div>
        </div>
      </div>

      <section className="Card PageSection">
        <div className="Card__header">
          <h2 className="Card__title">Редактировать профиль</h2>
        </div>
        <div className="Card__body">
          <form className="ProfileForm FormStack" onSubmit={saveProfile}>
            <div className="Field Field--full">
              <label className="Field__label">ФИО</label>
              <input
                className="Input"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
                minLength={2}
              />
            </div>
            <div className="Field Field--full">
              <label className="Field__label">Факультет</label>
              <input
                className="Input"
                value={editFaculty}
                onChange={(e) => setEditFaculty(e.target.value)}
                placeholder="Не указан"
              />
            </div>
            {editError && <Alert variant="error">{editError}</Alert>}
            {editMsg && <Alert variant="success">{editMsg}</Alert>}
            <div className="FormActions">
              <button type="submit" className="Btn Btn--primary">
                Сохранить
              </button>
            </div>
          </form>
        </div>
      </section>

      {balances && (
        <div className="HomePage__stats PageSection">
          <div className="Card HomePage__stat-card">
            <p className="HomePage__stat-label">Всего</p>
            <p className="HomePage__stat-value">{formatTkn(balances.total)}</p>
          </div>
          <div className="Card HomePage__stat-card">
            <p className="HomePage__stat-label">Доступно</p>
            <p className="HomePage__stat-value">{formatTkn(balances.available)}</p>
          </div>
          <div className="Card HomePage__stat-card">
            <p className="HomePage__stat-label">Заморожено</p>
            <p className="HomePage__stat-value">{formatTkn(balances.frozen)}</p>
          </div>
          {balances.pending_refund > 0 && (
            <div className="Card HomePage__stat-card">
              <p className="HomePage__stat-label">Ожидает возврата</p>
              <p className="HomePage__stat-value">{formatTkn(balances.pending_refund)}</p>
            </div>
          )}
          {profile?.stats && (
            <>
              <div className="Card HomePage__stat-card">
                <p className="HomePage__stat-label">Участий</p>
                <p className="HomePage__stat-value">{profile.stats.auction_participations}</p>
              </div>
              <div className="Card HomePage__stat-card">
                <p className="HomePage__stat-label">Побед</p>
                <p className="HomePage__stat-value">{profile.stats.won_auctions}</p>
              </div>
            </>
          )}
        </div>
      )}

      {balances?.by_project?.length > 0 && (
        <section className="Card PageSection">
          <div className="Card__header">
            <h2 className="Card__title">Баланс по проектам</h2>
          </div>
          <div className="Card__body">
            <div className="TableWrap">
              <table className="Table">
                <thead>
                  <tr>
                    <th>Проект</th>
                    <th>Доступно</th>
                    <th>Заморожено</th>
                  </tr>
                </thead>
                <tbody>
                  {balances.by_project.map((p) => (
                    <tr key={p.project_id}>
                      <td>
                        <Link to={`/projects/${p.project_id}`}>{p.project_name}</Link>
                      </td>
                      <td>{formatTkn(p.available)}</td>
                      <td>{formatTkn(p.frozen)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      <section className="Card PageSection">
        <div className="Card__header">
          <h2 className="Card__title">Активность</h2>
        </div>
        <div className="Card__body">
          {activity.length === 0 ? (
            <EmptyState title="Нет событий" />
          ) : (
            <ul className="ActivityList">
              {activity.map((a) => (
                <li key={a.id} className="ActivityList__item">
                  <strong>{a.title}</strong>
                  <span>{a.description}</span>
                  <time>{new Date(a.created_at).toLocaleString('ru-RU')}</time>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <div className="HomePage__actions">
        <Link to="/projects" className="Btn Btn--secondary">
          Мои проекты
        </Link>
        <Link to="/auctions" className="Btn Btn--secondary">
          Аукционы
        </Link>
        <Link to="/transfers" className="Btn Btn--secondary">
          Переводы
        </Link>
      </div>
    </>
  );
}
