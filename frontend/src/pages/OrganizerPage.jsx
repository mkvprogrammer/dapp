import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi } from '../api';
import { ApiError } from '../api/client';
import CreateProjectForm from '../components/CreateProjectForm';
import Alert from '../components/ui/Alert';
import EmptyState from '../components/ui/EmptyState';
import LoadingBlock from '../components/ui/LoadingBlock';
import { useAuth } from '../context/AuthContext';
import { formatTkn, isProjectOrganizer } from '../utils/format';

export default function OrganizerPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [joinCode, setJoinCode] = useState('');
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsApi.list().then(setProjects);
  }, []);

  const myProjects =
    user?.role === 'admin' ? projects : projects.filter((p) => isProjectOrganizer(p, user));

  useEffect(() => {
    if (!selectedId && myProjects.length > 0) {
      setSelectedId(String(myProjects[0].id));
    }
  }, [myProjects, selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    setMembersLoading(true);
    setError('');
    const pid = Number(selectedId);
    projectsApi.get(pid).then((p) => setJoinCode(p.join_code || ''));
    projectsApi.organizerStats(pid).then(setStats).catch(() => setStats(null));
    projectsApi
      .members(pid)
      .then(setMembers)
      .catch((err) => {
        setMembers([]);
        setError(err instanceof ApiError ? err.message : 'Не удалось загрузить участников');
      })
      .finally(() => setMembersLoading(false));
  }, [selectedId]);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Панель организатора</h1>
          <p className="PageHeader__subtitle">
            Участники, начисление токенов и подтверждение посещения на странице аукциона.
          </p>
        </div>
        {user?.role === 'admin' && (
          <Link to="/admin" className="Btn Btn--secondary">
            Админ-панель
          </Link>
        )}
      </header>

      {user?.role === 'organizer' && (
        <section className="Card PageSection">
          <div className="Card__header">
            <h2 className="Card__title">Создать проект</h2>
          </div>
          <div className="Card__body">
            <CreateProjectForm onCreated={() => projectsApi.list().then(setProjects)} />
          </div>
        </section>
      )}

      <div className="OrganizerPage__actions-row">
        <Link to="/create-auction" className="Btn Btn--primary">
          Создать аукцион
        </Link>
        <Link to="/auctions" className="Btn Btn--secondary">
          Аукционы и посещаемость
        </Link>
      </div>

      {stats && (
        <section className="Card PageSection">
          <div className="Card__header">
            <h2 className="Card__title">Статистика: {stats.project_name}</h2>
          </div>
          <div className="Card__body">
            <div className="HomePage__stats">
              <div className="Card HomePage__stat-card">
                <p className="HomePage__stat-label">Участников</p>
                <p className="HomePage__stat-value">{stats.members_count}</p>
              </div>
              <div className="Card HomePage__stat-card">
                <p className="HomePage__stat-label">Токенов в обороте</p>
                <p className="HomePage__stat-value">{formatTkn(stats.tokens_in_circulation)}</p>
              </div>
              <div className="Card HomePage__stat-card">
                <p className="HomePage__stat-label">Активных аукционов</p>
                <p className="HomePage__stat-value">{stats.active_auctions_count}</p>
              </div>
              <div className="Card HomePage__stat-card">
                <p className="HomePage__stat-label">Посещаемость</p>
                <p className="HomePage__stat-value">{stats.average_attendance_percent}%</p>
              </div>
            </div>
            <div className="OrganizerPage__charts-inline">
              <div>
                <p className="Field__label">Записи за 7 дней</p>
                <ul className="OrganizerPage__mini-list">
                  {(stats.weekly_mints || []).map((d) => (
                    <li key={d.date}>
                      {d.date}: {d.count}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="Field__label">Аукционы за 7 дней</p>
                <ul className="OrganizerPage__mini-list">
                  {(stats.auction_activity_by_day || []).map((d) => (
                    <li key={d.date}>
                      {d.date}: {d.count}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="Card PageSection">
        <div className="Card__header">
          <h2 className="Card__title">Участники проекта</h2>
        </div>
        <div className="Card__body">
          {myProjects.length === 0 ? (
            <EmptyState title="Нет проектов для управления">
              Создайте проект выше, чтобы выдавать коды записи и начислять TKN.
            </EmptyState>
          ) : (
            <>
              <div className="Field Field--full Field--narrow">
                <label className="Field__label">Проект</label>
                <select className="Select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                  {myProjects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
              {joinCode && (
                <p className="OrganizerPage__join-code">
                  Код для записи студентов: <strong>{joinCode}</strong>
                </p>
              )}
              {error && <Alert variant="error">{error}</Alert>}
              {membersLoading && <LoadingBlock />}
              {!membersLoading && members.length > 0 && (
                <div className="TableWrap TableWrap--spaced">
                  <table className="Table">
                    <thead>
                      <tr>
                        <th>ITMO ID</th>
                        <th>ФИО</th>
                        <th>Баланс</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {members.map((m) => (
                        <tr key={m.user_id}>
                          <td>{m.student_id}</td>
                          <td>{m.full_name}</td>
                          <td>{formatTkn(m.token_balance)}</td>
                          <td>
                            <MintTokensButton
                              projectId={Number(selectedId)}
                              member={m}
                              onDone={() => projectsApi.members(Number(selectedId)).then(setMembers)}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {!membersLoading && members.length === 0 && !error && (
                <EmptyState inline title="Нет записанных студентов">
                  Поделитесь кодом проекта — студенты появятся в таблице после записи.
                </EmptyState>
              )}
            </>
          )}
        </div>
      </section>

      {myProjects.length > 0 && (
        <section className="Card">
          <div className="Card__header">
            <h2 className="Card__title">Проекты</h2>
          </div>
          <div className="Card__body">
            <ul className="OrganizerPage__mini-list">
              {myProjects.map((p) => (
                <li key={p.id}>
                  <Link to={`/projects/${p.id}`}>{p.name}</Link> — {p.is_active ? 'активен' : 'неактивен'}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </>
  );
}

function MintTokensButton({ projectId, member, onDone }) {
  const [amount, setAmount] = useState('100');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const submit = async () => {
    setBusy(true);
    setMsg('');
    try {
      await projectsApi.mintTokens(projectId, member.user_id, { amount: Number(amount) });
      setMsg('Начислено');
      onDone();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : 'Ошибка');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="MintRow">
      <input
        className="Input"
        type="number"
        min="1"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        aria-label="Сумма TKN"
      />
      <button type="button" className="Btn Btn--secondary Btn--sm" disabled={busy} onClick={submit}>
        + TKN
      </button>
      {msg && <span className="MintRow__msg">{msg}</span>}
    </div>
  );
}
