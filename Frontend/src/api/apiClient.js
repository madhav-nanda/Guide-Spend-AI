/**
 * Centralized API client.
 * Every HTTP call in the app goes through this single axios instance.
 *
 * Responsibilities:
 *  - Attach JWT from localStorage to every request
 *  - Redirect to /login on 401 (expired/invalid token)
 *  - Normalize non-OK responses into a consistent { message } error shape
 *  - Base URL configurable via VITE_API_URL (defaults to /api for Vite proxy)
 */
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT ──
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 + normalize errors ──
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    // Only redirect on 401 if a token existed (session expired).
    // Login/register 401s are credential failures — let the caller handle them.
    if (status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }

    // Build a consistent error object for callers
    const message =
      error.response?.data?.error ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    return Promise.reject({ message, status });
  }
);

export default apiClient;
