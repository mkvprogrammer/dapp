import { NavLink } from 'react-router-dom';
import BrandLogo from './BrandLogo';
import { SIDEBAR_NAV } from './icons/Icons';

export default function AppSidebar() {
  return (
    <aside className="AppSidebar">
      <NavLink to="/" className="AppSidebar__brand">
        <BrandLogo className="AppSidebar__logo" width={40} height={40} />
        <div className="AppSidebar__brand-text">
          <p className="AppSidebar__brand-name">AuctionChain</p>
          <p className="AppSidebar__brand-tagline">Честное распределение ресурсов</p>
        </div>
      </NavLink>
      <nav>
        <ul className="AppSidebar__nav">
          {SIDEBAR_NAV.map(({ to, label, Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  `AppSidebar__link${isActive ? ' AppSidebar__link--active' : ''}`
                }
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
        <a href="#docs" className="Btn Btn--secondary Btn--sm Btn--block">
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
