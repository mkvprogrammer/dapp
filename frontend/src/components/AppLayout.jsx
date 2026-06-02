import { Outlet } from 'react-router-dom';
import AppSidebar from './AppSidebar';
import AppTopbar from './AppTopbar';

export default function AppLayout({ pageClass = '' }) {
  return (
    <div className={`AppLayout ${pageClass}`.trim()}>
      <AppSidebar />
      <div className="AppLayout__main">
        <AppTopbar />
        <main className="AppLayout__content">
          <Outlet />
        </main>
      </div>
      <nav className="AppMobileNav" aria-label="Мобильная навигация">
        <a href="/" className="AppMobileNav__link">
          Главная
        </a>
        <a href="/profile" className="AppMobileNav__link">
          Профиль
        </a>
        <a href="/auctions" className="AppMobileNav__link">
          Аукционы
        </a>
        <a href="/projects" className="AppMobileNav__link">
          Проекты
        </a>
        <a href="/notifications" className="AppMobileNav__link">
          Ещё
        </a>
      </nav>
    </div>
  );
}
