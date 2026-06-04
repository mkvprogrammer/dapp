export function getInitials(fullName) {
  if (!fullName) return '?';
  return fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || '')
    .join('');
}

export function formatTkn(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—';
  return `${n.toFixed(2)} TKN`;
}

export function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

export function formatTimeLeft(endIso) {
  if (!endIso) return '—';
  const diff = new Date(endIso) - Date.now();
  if (diff <= 0) return 'Завершён';
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  if (h > 24) return `${Math.floor(h / 24)} д ${h % 24} ч`;
  if (h > 0) return `${h} ч ${m} мин`;
  return `${m} мин`;
}

export function firstName(fullName) {
  const parts = fullName?.trim().split(/\s+/) || [];
  return parts[1] || parts[0] || 'пользователь';
}

const PROJECT_ICONS = ['math', 'physics', 'programming', 'chemistry'];
const PROJECT_GLYPHS = { math: 'Σ', physics: '⚛', programming: '</>', chemistry: '⚗' };

export function projectStyle(id) {
  const idx = Math.abs(Number(id) || 0) % PROJECT_ICONS.length;
  const key = PROJECT_ICONS[idx];
  const colors = ['#6c4dff', '#3b82f6', '#22c55e', '#f59e0b'];
  return {
    iconClass: `ProjectIcon ProjectIcon--${key}`,
    glyph: PROJECT_GLYPHS[key],
    color: colors[idx],
    barWidth: `${40 + (idx * 15)}%`,
  };
}

export function roleLabel(role) {
  const map = { student: 'Участник', organizer: 'Организатор', admin: 'Админ' };
  return map[role] || role;
}

/** UUID пользователя из /auth/me (user_id или legacy id). */
export function authUserId(user) {
  if (!user) return null;
  const id = user.user_id ?? user.id;
  return id != null ? String(id) : null;
}

export function isOrganizerRole(role) {
  return role === 'organizer' || role === 'admin';
}

export function isProjectOrganizer(project, user) {
  const uid = authUserId(user);
  if (!uid || !project?.organizer_id) return false;
  return String(project.organizer_id) === uid;
}
