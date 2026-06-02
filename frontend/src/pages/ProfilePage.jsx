import { Link } from 'react-router-dom';
import ApiNotice from '../components/ApiNotice';
import { useAuth } from '../context/AuthContext';
import { getInitials, roleLabel } from '../utils/format';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <>
      <header className="PageHeader">
        <h1 className="PageHeader__title">Личный кабинет</h1>
        <p className="PageHeader__subtitle">Профиль, баланс и активность на платформе.</p>
      </header>

      <ApiNotice>
        Расширенный профиль (email, факультет, статистика побед, замороженный баланс, лента активности) требует отдельных
        эндпоинтов — сейчас доступен только GET /auth/me.
      </ApiNotice>

      <div className="Card" style={{ marginBottom: 24 }}>
        <div className="Card__body" style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <span className="Avatar Avatar--lg">{getInitials(user?.full_name)}</span>
          <div>
            <h2 style={{ margin: 0 }}>{user?.full_name}</h2>
            <p style={{ margin: '4px 0', color: 'var(--color-text-muted)' }}>
              {roleLabel(user?.role)} · ITMO ID: {user?.student_id}
            </p>
            <p style={{ margin: 0, fontSize: '0.8125rem', wordBreak: 'break-all' }}>
              Кошелёк: {user?.wallet_address}
            </p>
          </div>
        </div>
      </div>

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
