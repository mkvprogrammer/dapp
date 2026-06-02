import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { adminApi, fetchHealth } from '../api';
import ApiNotice from '../components/ApiNotice';
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

      <ApiNotice>
        Реализован только PUT /admin/users/{'{user_id}'}/role. Для макета нужны: GET /admin/users, GET /admin/audit-log,
        POST /admin/emergency-stop, расширенный GET /health.
      </ApiNotice>

      <div className="AdminPage__emergency">
        <div className="AdminPage__emergency-text">
          <h3>Экстренная остановка</h3>
          <p>Приостанавливает все активные аукционы. API не реализован.</p>
        </div>
        <button type="button" className="Btn Btn--danger" disabled>
          Остановить все аукционы
        </button>
      </div>

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

      <section className="Card">
        <div className="Card__header">
          <h2 className="Card__title">Смена роли (демо)</h2>
        </div>
        <div className="Card__body">
          <p>
            Текущий пользователь: {user?.full_name} ({user?.role}). Для смены роли другого пользователя укажите UUID и
            новую роль в API-клиенте или расширьте UI после появления GET /admin/users.
          </p>
          <RoleChangeForm />
        </div>
      </section>
    </>
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
