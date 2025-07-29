import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Don't try to refresh if we're already on login/register pages or if no token exists
      const currentToken = localStorage.getItem('access_token');
      if (!currentToken || originalRequest.url?.includes('/auth/')) {
        localStorage.removeItem('access_token');
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      try {
        const response = await api.post('/api/auth/refresh');
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/api/auth/token', 
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ),
  register: (userData) => api.post('/api/auth/register', userData),
  getMe: () => api.get('/api/auth/me'),
  refresh: () => api.post('/api/auth/refresh'),
};

// Agent API
export const agentAPI = {
  execute: (data) => api.post('/api/agents/execute', data),
  getInfo: () => api.get('/api/agents/info'),
  getHistory: (params) => api.get('/api/agents/actions/history', { params }),
  getActionDetail: (actionId) => api.get(`/api/agents/actions/${actionId}`),
  overrideAction: (actionId, data) => api.post(`/api/agents/actions/${actionId}/override`, data),
};

// Employee API
export const employeeAPI = {
  list: (params) => api.get('/api/employees', { params }),
  get: (id) => api.get(`/api/employees/${id}`),
  update: (id, data) => api.put(`/api/employees/${id}`, data),
  getAttendance: (id, params) => api.get(`/api/employees/${id}/attendance`, { params }),
};

// Task API
export const taskAPI = {
  list: (params) => api.get('/api/tasks', { params }),
  create: (data) => api.post('/api/tasks', data),
  get: (id) => api.get(`/api/tasks/${id}`),
  update: (id, data) => api.put(`/api/tasks/${id}`, data),
  assign: (id, assigneeId) => api.post(`/api/tasks/${id}/assign`, null, { params: { assignee_id: assigneeId } }),
  addComment: (id, comment) => api.post(`/api/tasks/${id}/comments`, { comment }),
};

// Report API
export const reportAPI = {
  generate: (data) => api.post('/api/reports/generate', data),
  list: (params) => api.get('/api/reports', { params }),
  get: (id) => api.get(`/api/reports/${id}`),
};

export default api;