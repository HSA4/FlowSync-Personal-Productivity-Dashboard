/** API Service for FlowSync */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response) {
      const { status, data } = error.response;

      // Handle 401 unauthorized - redirect to login
      if (status === 401 && window.location.pathname !== '/login') {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }

      // Handle 429 rate limit
      if (status === 429) {
        const retryAfter = data?.error?.details?.retry_after;
        console.warn(`Rate limited. Retry after ${retryAfter || 'a few'} seconds.`);
      }

      // Handle 500 server errors
      if (status >= 500) {
        console.error('Server error:', data?.error?.message || 'An unexpected error occurred');
      }
    }

    return Promise.reject(error);
  }
);

// API Methods
export const apiService = {
  // Health check
  health: () => api.get('/health'),

  // Tasks
  getTasks: (params = {}) => api.get('/api/v1/tasks', { params }),
  getTask: (id) => api.get(`/api/v1/tasks/${id}`),
  createTask: (data) => api.post('/api/v1/tasks', data),
  updateTask: (id, data) => api.put(`/api/v1/tasks/${id}`, data),
  deleteTask: (id) => api.delete(`/api/v1/tasks/${id}`),
  toggleTask: (id) => api.patch(`/api/v1/tasks/${id}/toggle`),

  // Events
  getEvents: (params = {}) => api.get('/api/v1/events', { params }),
  getEvent: (id) => api.get(`/api/v1/events/${id}`),
  createEvent: (data) => api.post('/api/v1/events', data),
  updateEvent: (id, data) => api.put(`/api/v1/events/${id}`, data),
  deleteEvent: (id) => api.delete(`/api/v1/events/${id}`),
};

export default api;
