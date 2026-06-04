import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLayout } from '../context/LayoutContext';
import { isOrganizerRole } from '../utils/format';
import BrandLogo from './BrandLogo';
import { IconClose, SIDEBAR_NAV } from './icons/Icons';

const ORGANIZER_ONLY = new Set(['/organizer', '/create-auction']);

export default function AppSidebar() {
  const { user } = useAuth();
  const { closeSidebar } = useLayout();
  const navItems = SIDEBAR_NAV.filter(
    (item) => !ORGANIZER_ONLY.has(item.to) || isOrganizerRole(user?.role),
  );

  return (
    <aside className="AppSidebar" id="app-sidebar">
      <div className="AppSidebar__header">
        <NavLink to="/" className="AppSidebar__brand" onClick={closeSidebar}>
          <BrandLogo className="AppSidebar__logo" width={40} height={40} />
          <div className="AppSidebar__brand-text">
            <p className="AppSidebar__brand-name">AuctionChain</p>
            <p className="AppSidebar__brand-tagline">Честное распределение ресурсов</p>
          </div>
        </NavLink>
        <button
          type="button"
          className="AppSidebar__closeBtn"
          aria-label="Закрыть меню"
          onClick={closeSidebar}
        >
          <IconClose />
        </button>
      </div>
      <nav className="AppSidebar__nav-wrap">
        <ul className="AppSidebar__nav">
          {navItems.map(({ to, label, Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  `AppSidebar__link${isActive ? ' AppSidebar__link--active' : ''}`
                }
                onClick={closeSidebar}
              >
                <Icon />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="AppSidebar__help">
        <p className="AppSidebar__help-title">Нужна помощь?</p>
        <p className="AppSidebar__help-text">Ознакомьтесь с документацией платформы</p>
        <a href="#docs" className="Btn Btn--secondary Btn--sm Btn--block" onClick={closeSidebar}>
          Документация
        </a>
      </div>
      <p className="AppSidebar__footer">
        &copy; 2026 AuctionChain
        <br />
        v0.1.0
      </p>
    </aside>
  );
}
