const svgProps = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  'aria-hidden': true,
};

export function IconHome(props) {
  return (
    <svg {...svgProps} {...props}>
      <path d="M3 10.5L12 4l9 6.5V20a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-9.5z" />
    </svg>
  );
}

export function IconProfile(props) {
  return (
    <svg {...svgProps} {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M5 20c0-4 3.1-7 7-7s7 3 7 7" />
    </svg>
  );
}

export function IconProjects(props) {
  return (
    <svg {...svgProps} {...props}>
      <path d="M4 6h16M4 12h16M4 18h10" />
    </svg>
  );
}

export function IconAuctions(props) {
  return (
    <svg {...svgProps} {...props}>
      <path d="M14 4h6v6M10 20H4v-6M20 4l-8 8M4 20l8-8" />
    </svg>
  );
}

export function IconTransfers(props) {
  return (
    <svg {...svgProps} strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M7 16V4M7 4L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
    </svg>
  );
}

export function IconOrganizer(props) {
  return (
    <svg {...svgProps} {...props}>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 9h6M9 13h6M9 17h4" />
    </svg>
  );
}

export function IconCreateAuction(props) {
  return (
    <svg {...svgProps} {...props}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v8M8 12h8" />
    </svg>
  );
}

export function IconBell(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
      <path d="M18 8A6 6 0 106 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" />
    </svg>
  );
}

export function IconChevronDown(props) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

export function IconShieldCheck(props) {
  return (
    <svg {...svgProps} {...props}>
      <path d="M12 3L4 7v5c0 5 3.5 9 8 10 4.5-1 8-5 8-10V7l-8-4z" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconTokens(props) {
  return (
    <svg {...svgProps} {...props}>
      <ellipse cx="12" cy="6" rx="8" ry="3" />
      <path d="M4 6v4c0 1.7 3.6 3 8 3s8-1.3 8-3V6" />
      <path d="M4 14v4c0 1.7 3.6 3 8 3s8-1.3 8-3v-4" />
    </svg>
  );
}

export function IconUsers(props) {
  return (
    <svg {...svgProps} {...props}>
      <circle cx="9" cy="8" r="3" />
      <circle cx="17" cy="10" r="2.5" />
      <path d="M3 20c0-3 2.7-5 6-5s6 2 6 5" strokeLinecap="round" />
      <path d="M15 20c0-2 1.5-3.5 4-3.5" strokeLinecap="round" />
    </svg>
  );
}

export function IconItmoId(props) {
  return (
    <svg {...svgProps} {...props}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <circle cx="9" cy="12" r="2" />
      <path d="M15 10h4M15 14h4" strokeLinecap="round" />
    </svg>
  );
}

export function IconLock(props) {
  return (
    <svg {...svgProps} {...props}>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V8a4 4 0 018 0v3" strokeLinecap="round" />
    </svg>
  );
}

export function IconUser(props) {
  return (
    <svg {...svgProps} {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M5 20c0-4 3.1-7 7-7s7 3 7 7" strokeLinecap="round" />
    </svg>
  );
}

export const AUTH_FEATURES = [
  { Icon: IconShieldCheck, label: 'Честные аукционы' },
  { Icon: IconTokens, label: 'Токены за активность' },
  { Icon: IconUsers, label: 'Прозрачные правила' },
];

export const SIDEBAR_NAV = [
  { to: '/', label: 'Главная', Icon: IconHome, end: true },
  { to: '/profile', label: 'Личный кабинет', Icon: IconProfile },
  { to: '/projects', label: 'Мои проекты', Icon: IconProjects },
  { to: '/auctions', label: 'Аукционы', Icon: IconAuctions },
  { to: '/transfers', label: 'Переводы токенов', Icon: IconTransfers },
  { to: '/organizer', label: 'Организатору', Icon: IconOrganizer },
  { to: '/create-auction', label: 'Создать аукцион', Icon: IconCreateAuction },
];
