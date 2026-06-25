const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken() {
  return localStorage.getItem('token');
}

async function api(path: string, options: RequestInit = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken() || ''}`,
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/';
    return null;
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err);
  }
  return res.json();
}

export const auth = {
  login: (email: string, password: string) =>
    api('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username: email, password }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (data: any) => api('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  me: () => api('/auth/me'),
};

export const crm = {
  connect: (type: string) => api(`/crm/connect/${type}`),
  connections: () => api('/crm/connections'),
  trigger: (connectionId: string) => api('/cleaning/trigger', { method: 'POST', body: JSON.stringify({ connection_id: connectionId }) }),
};

export const cleaning = {
  jobs: () => api('/cleaning/jobs'),
  settings: () => api('/cleaning/settings'),
  updateSettings: (data: any) => api('/cleaning/settings', { method: 'PUT', body: JSON.stringify(data) }),
};

export const billing = {
  usage: () => api('/billing/usage'),
  checkout: () => api('/billing/checkout', { method: 'POST' }),
  portal: () => api('/billing/portal', { method: 'POST' }),
};

export const audit = {
  changes: (page = 1) => api(`/audit/changes?page=${page}`),
  rollback: (changeId: string) => api(`/audit/rollback/${changeId}`, { method: 'POST' }),
};
