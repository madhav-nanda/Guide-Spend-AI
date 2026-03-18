/**
 * Auth domain API.
 * Encapsulates /register, /login, /protected.
 * Components call these functions — never axios directly.
 */
import apiClient from './apiClient';

export const authApi = {
  /**
   * Register a new user.
   * @returns {{ message: string }}
   */
  async register(username, email, password) {
    const res = await apiClient.post('/register', { username, email, password });
    return res.data;
  },

  /**
   * Login and receive a JWT.
   * @returns {{ access_token: string }}
   */
  async login(email, password) {
    const res = await apiClient.post('/login', { email, password });
    return res.data;
  },

  /**
   * Verify the stored token is still valid.
   * @returns {{ logged_in_as: string }}
   */
  async verifyToken() {
    const res = await apiClient.get('/protected');
    return res.data;
  },
};
