import { apiRequest, getAccessToken, API_BASE } from './client';

export const authApi = {
  register: (body) => apiRequest('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(body), auth: false }),
  login: (body) => apiRequest('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(body), auth: false }),
  logout: (refreshToken) =>
    apiRequest('/api/v1/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }),
  me: () => apiRequest('/api/v1/auth/me'),
};

export const dashboardApi = {
  get: () => apiRequest('/api/v1/dashboard'),
};

export const usersApi = {
  myProjects: () => apiRequest('/api/v1/users/me/projects'),
  profile: () => apiRequest('/api/v1/users/me/profile'),
  updateProfile: (body) =>
    apiRequest('/api/v1/users/me/profile', { method: 'PATCH', body: JSON.stringify(body) }),
  balances: () => apiRequest('/api/v1/users/me/balances'),
  activity: (limit = 20, offset = 0) =>
    apiRequest(`/api/v1/users/me/activity?limit=${limit}&offset=${offset}`),
  activeAuctions: () => apiRequest('/api/v1/users/me/auctions/active'),
};

export const projectsApi = {
  list: () => apiRequest('/api/v1/projects/'),
  my: () => apiRequest('/api/v1/users/me/projects'),
  get: (id) => apiRequest(`/api/v1/projects/${id}`),
  create: (body) => apiRequest('/api/v1/projects/', { method: 'POST', body: JSON.stringify(body) }),
  enroll: (projectId) => apiRequest(`/api/v1/projects/${projectId}/enroll`, { method: 'POST', body: '{}' }),
  joinByCode: (code) =>
    apiRequest('/api/v1/projects/join-by-code', { method: 'POST', body: JSON.stringify({ code }) }),
  members: (projectId) => apiRequest(`/api/v1/projects/${projectId}/members`),
  balance: (projectId) => apiRequest(`/api/v1/projects/${projectId}/balance`),
  organizerStats: (projectId) => apiRequest(`/api/v1/projects/${projectId}/organizer/stats`),
  attendanceStats: (projectId) => apiRequest(`/api/v1/projects/${projectId}/attendance/stats`),
  mintTokens: (projectId, userId, body) =>
    apiRequest(`/api/v1/projects/${projectId}/members/${userId}/mint-tokens`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

export const auctionsApi = {
  list: (params = {}) => {
    const q = new URLSearchParams();
    if (params.project_id != null) q.set('project_id', params.project_id);
    if (params.status) q.set('status', params.status);
    if (params.search) q.set('search', params.search);
    const qs = q.toString();
    return apiRequest(qs ? `/api/v1/auctions/?${qs}` : '/api/v1/auctions/');
  },
  get: (id) => apiRequest(`/api/v1/auctions/${id}`),
  leaderboard: (id, limit = 20) => apiRequest(`/api/v1/auctions/${id}/leaderboard?limit=${limit}`),
  bidHistory: (id) => apiRequest(`/api/v1/auctions/${id}/bid-history`),
  create: (body) => apiRequest('/api/v1/auctions/', { method: 'POST', body: JSON.stringify(body) }),
  bid: (id, body) => apiRequest(`/api/v1/auctions/${id}/bid`, { method: 'POST', body: JSON.stringify(body) }),
  cancelBid: (id, body) =>
    apiRequest(`/api/v1/auctions/${id}/bid`, { method: 'DELETE', body: JSON.stringify(body) }),
  attendance: (id) => apiRequest(`/api/v1/auctions/${id}/attendance`),
  confirmAttendance: (id, body) =>
    apiRequest(`/api/v1/auctions/${id}/attendance/confirm`, { method: 'POST', body: JSON.stringify(body) }),
  markAbsent: (id, body) =>
    apiRequest(`/api/v1/auctions/${id}/attendance/mark-absent`, { method: 'POST', body: JSON.stringify(body) }),
  closeDay: (id, body) =>
    apiRequest(`/api/v1/auctions/${id}/attendance/close-day`, { method: 'POST', body: JSON.stringify(body) }),
};

export const transfersApi = {
  create: (body) => apiRequest('/api/v1/transfers', { method: 'POST', body: JSON.stringify(body) }),
  list: (params = {}) => {
    const q = new URLSearchParams(params);
    return apiRequest(`/api/v1/transfers?${q}`);
  },
  recentRecipients: () => apiRequest('/api/v1/transfers/recent-recipients'),
  exportCsv: async () => {
    const token = getAccessToken();
    const res = await fetch(`${API_BASE}/api/v1/transfers/export`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error('Не удалось выгрузить CSV');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transfers-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  },
};

export const uploadsApi = {
  image: async (file) => {
    const token = getAccessToken();
    const body = new FormData();
    body.append('file', file);
    const res = await fetch(`${API_BASE}/api/v1/uploads/images`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = typeof data.detail === 'string' ? data.detail : 'Ошибка загрузки';
      throw new Error(detail);
    }
    return data;
  },
};

export const notificationsApi = {
  list: (params = {}) => {
    const q = new URLSearchParams(params);
    return apiRequest(`/api/v1/notifications?${q}`);
  },
  markRead: (id) => apiRequest(`/api/v1/notifications/${id}/read`, { method: 'PATCH', body: '{}' }),
  markAllRead: () => apiRequest('/api/v1/notifications/read-all', { method: 'PATCH', body: '{}' }),
};

export const walletApi = {
  balance: (projectId) => {
    const q = projectId != null ? `?project_id=${projectId}` : '';
    return apiRequest(`/api/v1/wallet/balance${q}`);
  },
  demoTopUp: (projectId, amount = 100) =>
    apiRequest(`/api/v1/wallet/demo-top-up?project_id=${projectId}&amount=${amount}`, { method: 'POST' }),
};

export const adminApi = {
  listUsers: (search) => {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiRequest(`/api/v1/admin/users${q}`);
  },
  auditLog: (eventType) => {
    const q = eventType ? `?event_type=${eventType}` : '';
    return apiRequest(`/api/v1/admin/audit-log${q}`);
  },
  health: () => apiRequest('/api/v1/admin/health'),
  emergencyStop: (reason) =>
    apiRequest('/api/v1/admin/emergency-stop', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  changeRole: (userId, newRole) =>
    apiRequest(`/api/v1/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ new_role: newRole }),
    }),
};

export async function fetchHealth() {
  const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/health`);
  return res.json();
}
