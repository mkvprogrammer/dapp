import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { adminApi, fetchHealth } from '../api';
import { ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function AdminPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth({ status: 'error' }));
  }, []);

  return (
    <>
      <header className="PageHeader PageHeader__row">
        <div>
          <h1 className="PageHeader__title">Админ-панель</h1>
          <p className="PageHeader__subtitle">Мониторинг системы, управление пользователями и аудит.</p>
        </div>
        <Link to="/organizer" className="Btn Btn--secondary">
          ← Организатору
        </Link>
      </header>

      <EmergencyStopBlock />

      <AdminHealthPanel />

      <section aria-label="Состояние системы" className="AdminPage__health">
        <div className="Card AdminPage__health-card">
          <div className="AdminPage__health-status">
            <span className={`AdminPage__health-dot AdminPage__health-dot--${health?.status === 'ok' ? 'ok' : 'warn'}`} />
            {health?.status === 'ok' ? 'Работает' : 'Проверка…'}
          </div>
          <p className="AdminPage__health-name">API /health</p>
          <p className="AdminPage__health-detail">БД: {health?.database ?? '—'}</p>
        </div>
      </section>

      <section className="Card" style={{ marginBottom: 24 }}>
        <div className="Card__header">
          <h2 className="Card__title">Пользователи</h2>
        </div>
        <div className="Card__body">
          <UsersTable />
        </div>
      </section>

      <section className="Card" style={{ marginBottom: 24 }}>
        <div className="Card__header">
          <h2 className="Card__title">Журнал аудита</h2>
        </div>
        <div className="Card__body">
          <AuditLogTable />
        </div>
      </section>

      <section className="Card">
        <div className="Card__header">
          <h2 className="Card__title">Смена роли</h2>
        </div>
        <div className="Card__body">
          <p style={{ marginBottom: 12 }}>
            Текущий пользователь: {user?.full_name} ({user?.role})
          </p>
          <RoleChangeForm />
        </div>
      </section>
    </>
  );
}

function AuditLogTable() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi
      .auditLog()
      .then((r) => setItems(r.items || []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Загрузка…</p>;
  if (!items.length) return <p>Записей пока нет</p>;

  return (
    <div className="TableWrap">
      <table className="Table">
        <thead>
          <tr>
            <th>Время</th>
            <th>Кто</th>
            <th>Действие</th>
            <th>Объект</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.id}>
              <td>{new Date(e.created_at).toLocaleString()}</td>
              <td>
                {e.actor_name}
                {e.actor_student_id ? ` (${e.actor_student_id})` : ''}
              </td>
              <td>{e.action}</td>
              <td style={{ fontSize: '0.75rem' }}>{e.object_ref}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UsersTable() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    adminApi
      .listUsers(search || undefined)
      .then((r) => setUsers(r.items || []))
      .finally(() => setLoading(false));
  }, [search]);

  return (
    <>
      <div className="Field Field--full" style={{ maxWidth: 320, marginBottom: 12 }}>
        <label className="Field__label">Поиск</label>
        <input
          className="Input"
          placeholder="ITMO ID или ФИО"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      {loading && <p>Загрузка…</p>}
      {!loading && (
        <div className="TableWrap">
          <table className="Table">
            <thead>
              <tr>
                <th>ITMO ID</th>
                <th>ФИО</th>
                <th>Роль</th>
                <th>Последний вход</th>
                <th>UUID</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id}>
                  <td>{u.student_id}</td>
                  <td>{u.full_name}</td>
                  <td>{u.role}</td>
                  <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—'}</td>
                  <td style={{ fontSize: '0.75rem' }}>{u.user_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function EmergencyStopBlock() {
  const [reason, setReason] = useState('');
  const [msg, setMsg] = useState('');

  const submit = async () => {
    if (reason.length < 10) {
      setMsg('Укажите причину (мин. 10 символов)');
      return;
    }
    try {
      const res = await adminApi.emergencyStop(reason);
      setMsg(res.message);
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : 'Ошибка');
    }
  };

  return (
    <div className="AdminPage__emergency" style={{ marginBottom: 24 }}>
      <div className="AdminPage__emergency-text">
        <h3>Экстренная остановка</h3>
        <p>Отменяет все открытые аукционы в БД (статус cancelled).</p>
      </div>
      <input
        className="Input"
        placeholder="Причина остановки"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        style={{ maxWidth: 400, marginBottom: 8 }}
      />
      <button type="button" className="Btn Btn--danger" onClick={submit}>
        Остановить все аукционы
      </button>
      {msg && <p style={{ marginTop: 8 }}>{msg}</p>}
    </div>
  );
}

function AdminHealthPanel() {
  const [health, setHealth] = useState(null);
  useEffect(() => {
    adminApi.health().then(setHealth).catch(() => setHealth(null));
  }, []);
  if (!health) return null;
  return (
    <section className="AdminPage__health" style={{ marginBottom: 24 }}>
      {health.services?.map((s) => (
        <div key={s.name} className="Card AdminPage__health-card">
          <p className="AdminPage__health-name">{s.name}</p>
          <p className="AdminPage__health-detail">
            {s.status} — {s.detail}
            {s.latency_ms != null ? ` (${s.latency_ms} ms)` : ''}
          </p>
        </div>
      ))}
      <p style={{ marginTop: 8 }}>
        Блок: {health.blockchain_block_number ?? '—'} · Активных аукционов: {health.active_auctions} · Ставок/час:{' '}
        {health.bids_per_hour}
      </p>
    </section>
  );
}

function RoleChangeForm() {
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState('student');
  const [msg, setMsg] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      const res = await adminApi.changeRole(userId, role);
      setMsg(`Роль обновлена: ${res.full_name} → ${res.role}`);
    } catch (err) {
      setMsg(err.message || 'Ошибка');
    }
  };

  return (
    <form onSubmit={submit} style={{ marginTop: 16, maxWidth: 480 }}>
      <div className="Field Field--full">
        <label className="Field__label">user_id (UUID)</label>
        <input className="Input" value={userId} onChange={(e) => setUserId(e.target.value)} required />
      </div>
      <div className="Field Field--full">
        <label className="Field__label">Новая роль</label>
        <select className="Select" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="student">student</option>
          <option value="organizer">organizer</option>
          <option value="admin">admin</option>
        </select>
      </div>
      <button type="submit" className="Btn Btn--primary" style={{ marginTop: 12 }}>
        Изменить роль
      </button>
      {msg && <p style={{ marginTop: 8 }}>{msg}</p>}
    </form>
  );
}
