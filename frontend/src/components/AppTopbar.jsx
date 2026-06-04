import { Link, useNavigate } from 'react-router-dom';
import { useLayout } from '../context/LayoutContext';
import { useNotifications } from '../context/NotificationsContext';
import { useAuth } from '../context/AuthContext';
import { getInitials, roleLabel } from '../utils/format';
import { IconBell, IconChevronDown, IconClose, IconMenu } from './icons/Icons';

export default function AppTopbar() {
  const { user, logout } = useAuth();
  const { sidebarOpen, toggleSidebar } = useLayout();
  const { unreadCount } = useNotifications();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="AppTopbar">
      <button
        type="button"
        className="AppTopbar__menuBtn"
        onClick={toggleSidebar}
        aria-expanded={sidebarOpen}
        aria-controls="app-sidebar"
        aria-label={sidebarOpen ? 'Закрыть меню' : 'Открыть меню'}
      >
        {sidebarOpen ? <IconClose /> : <IconMenu />}
      </button>

      <div className="AppTopbar__actions">
        <Link
          to="/notifications"
          className="AppTopbar__notify"
          aria-label={unreadCount > 0 ? `Уведомления: ${unreadCount} непрочитанных` : 'Уведомления'}
        >
          <IconBell />
          {unreadCount > 0 && (
            <span className="AppTopbar__notify-badge AppTopbar__notify-badge--count">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>
        <div className="AppTopbar__user">
          <span className="Avatar Avatar--sm">{getInitials(user?.full_name)}</span>
          <span className="AppTopbar__user-meta">
            <strong className="AppTopbar__user-name">{user?.full_name}</strong>
            <span className="AppTopbar__user-id">
              {user?.student_id}
              {user?.role && <span className="RoleBadge">{roleLabel(user.role)}</span>}
            </span>
          </span>
          <IconChevronDown className="AppTopbar__user-chevron" />
          <button type="button" className="Btn Btn--ghost Btn--sm AppTopbar__logout" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      </div>
    </header>
  );
}
