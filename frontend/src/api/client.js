export const API_BASE = import.meta.env.VITE_API_URL || '';

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredTokens() {
  const raw = localStorage.getItem('auctionchain_tokens');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredTokens(tokens) {
  if (tokens) {
    localStorage.setItem('auctionchain_tokens', JSON.stringify(tokens));
  } else {
    localStorage.removeItem('auctionchain_tokens');
  }
}

export function getAccessToken() {
  return getStoredTokens()?.access_token ?? null;
}

async function refreshAccessToken() {
  const tokens = getStoredTokens();
  if (!tokens?.refresh_token) return null;

  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  });

  if (!res.ok) {
    setStoredTokens(null);
    return null;
  }

  const data = await res.json();
  const next = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    token_type: data.token_type,
  };
  setStoredTokens(next);
  return next.access_token;
}

export async function apiRequest(path, options = {}) {
  const { auth = true, retry = true, ...fetchOptions } = options;
  const headers = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers || {}),
  };

  if (auth) {
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
  } catch (err) {
    const hint =
      API_BASE === ''
        ? 'Проверьте, что backend запущен (Docker: make up, API :8001; Vite: прокси на 8001 или VITE_DEV_API_TARGET=8000).'
        : `Не удалось подключиться к ${API_BASE}.`;
    throw new ApiError(
      err?.message?.includes('fetch') || err?.name === 'TypeError'
        ? `Сервер API недоступен. ${hint}`
        : err?.message || 'Ошибка сети',
      0,
      null,
    );
  }

  if (res.status === 401 && auth && retry) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.Authorization = `Bearer ${newToken}`;
      try {
        res = await fetch(`${API_BASE}${path}`, { ...fetchOptions, headers });
      } catch (err) {
        throw new ApiError('Сервер API недоступен при повторе запроса.', 0, null);
      }
    }
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    throw new ApiError(detail || res.statusText, res.status, data.detail);
  }

  return data;
}
