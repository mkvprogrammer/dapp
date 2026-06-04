import { useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { LayoutProvider, useLayout } from '../context/LayoutContext';
import { IconAuctions, IconBell, IconHome, IconMenu, IconProfile, IconProjects } from './icons/Icons';
import AppSidebar from './AppSidebar';
import AppTopbar from './AppTopbar';

const MOBILE_NAV = [
  { to: '/', label: 'Главная', Icon: IconHome, end: true },
  { to: '/auctions', label: 'Аукционы', Icon: IconAuctions },
  { to: '/projects', label: 'Проекты', Icon: IconProjects },
  { to: '/notifications', label: 'Алерты', Icon: IconBell },
];

function AppLayoutInner({ pageClass = '' }) {
  const location = useLocation();
  const { sidebarOpen, closeSidebar, openSidebar } = useLayout();

  useEffect(() => {
    closeSidebar();
  }, [location.pathname, closeSidebar]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') closeSidebar();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [closeSidebar]);

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 961px)');
    const onChange = () => {
      if (mq.matches) closeSidebar();
    };
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [closeSidebar]);

  useEffect(() => {
    document.body.classList.toggle('body--sidebar-open', sidebarOpen);
    return () => document.body.classList.remove('body--sidebar-open');
  }, [sidebarOpen]);

  const layoutClass = ['AppLayout', pageClass, sidebarOpen ? 'AppLayout--sidebar-open' : '']
    .filter(Boolean)
    .join(' ');

  return (
    <div className={layoutClass}>
      <button
        type="button"
        className="AppSidebar__backdrop"
        aria-label="Закрыть меню"
        tabIndex={sidebarOpen ? 0 : -1}
        onClick={closeSidebar}
      />
      <AppSidebar />
      <div className="AppLayout__main">
        <AppTopbar />
        <main className="AppLayout__content">
          <div className="PageShell">
            <Outlet />
          </div>
        </main>
      </div>
      <nav className="AppMobileNav" aria-label="Мобильная навигация">
        {MOBILE_NAV.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `AppMobileNav__link${isActive ? ' AppMobileNav__link--active' : ''}`
            }
          >
            <Icon />
            {label}
          </NavLink>
        ))}
        <button
          type="button"
          className={`AppMobileNav__link AppMobileNav__link--menu${sidebarOpen ? ' AppMobileNav__link--active' : ''}`}
          onClick={openSidebar}
          aria-expanded={sidebarOpen}
          aria-controls="app-sidebar"
        >
          <IconMenu />
          Меню
        </button>
      </nav>
    </div>
  );
}

export default function AppLayout(props) {
  return (
    <LayoutProvider>
      <AppLayoutInner {...props} />
    </LayoutProvider>
  );
}
