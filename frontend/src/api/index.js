import { apiRequest } from './client';

export const authApi = {
  register: (body) => apiRequest('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(body), auth: false }),
  login: (body) => apiRequest('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(body), auth: false }),
  logout: (refreshToken) =>
    apiRequest('/api/v1/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }),
  me: () => apiRequest('/api/v1/auth/me'),
};

export const projectsApi = {
  list: () => apiRequest('/api/v1/projects/'),
  get: (id) => apiRequest(`/api/v1/projects/${id}`),
  create: (body) => apiRequest('/api/v1/projects/', { method: 'POST', body: JSON.stringify(body) }),
  enroll: (projectId) => apiRequest(`/api/v1/projects/${projectId}/enroll`, { method: 'POST', body: '{}' }),
};

export const auctionsApi = {
  list: () => apiRequest('/api/v1/auctions/'),
  get: (id) => apiRequest(`/api/v1/auctions/${id}`),
  leaderboard: (id, limit = 20) => apiRequest(`/api/v1/auctions/${id}/leaderboard?limit=${limit}`),
  create: (body) => apiRequest('/api/v1/auctions/', { method: 'POST', body: JSON.stringify(body) }),
  bid: (id, body) => apiRequest(`/api/v1/auctions/${id}/bid`, { method: 'POST', body: JSON.stringify(body) }),
  cancelBid: (id, body) =>
    apiRequest(`/api/v1/auctions/${id}/bid`, { method: 'DELETE', body: JSON.stringify(body) }),
};

export const adminApi = {
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
