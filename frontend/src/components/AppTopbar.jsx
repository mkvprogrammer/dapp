import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getInitials } from '../utils/format';
import { IconBell, IconChevronDown } from './icons/Icons';

export default function AppTopbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="AppTopbar">
      <Link to="/notifications" className="AppTopbar__notify" aria-label="Уведомления">
        <IconBell />
        <span className="AppTopbar__notify-badge" />
      </Link>
      <div className="AppTopbar__user" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="Avatar Avatar--sm">{getInitials(user?.full_name)}</span>
        <span>
          <strong style={{ display: 'block', fontSize: '0.875rem' }}>{user?.full_name}</strong>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            itmo_id: {user?.student_id}
          </span>
        </span>
        <IconChevronDown />
        <button type="button" className="Btn Btn--ghost Btn--sm" onClick={handleLogout}>
          Выйти
        </button>
      </div>
    </header>
  );
}
