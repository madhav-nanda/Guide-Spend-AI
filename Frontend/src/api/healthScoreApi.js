/**
 * Health Score domain API.
 * Encapsulates the /v1/health-score endpoint.
 * Components call this via hooks — never apiClient directly.
 */
import apiClient from './apiClient';

export const healthScoreApi = {
  /**
   * Get the Financial Health Score.
   *
   * @param {Object} params
   * @param {string}  [params.account_id]       - plaid_account_id or omit for all
   * @param {number}  [params.window_days]      - 30, 60, or 90 (default 90)
   * @param {number}  [params.current_balance]  - real-time balance from Plaid
   */
  async getHealthScore(params = {}) {
    const query = {};
    if (params.account_id && params.account_id !== 'all') {
      query.account_id = params.account_id;
    }
    if (params.window_days) {
      query.window_days = params.window_days;
    }
    if (params.current_balance !== undefined && params.current_balance !== null) {
      query.current_balance = params.current_balance;
    }
    const res = await apiClient.get('/v1/health-score', { params: query });
    return res.data;
  },
};
