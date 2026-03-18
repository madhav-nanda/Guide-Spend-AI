/**
 * Cash flow forecast domain API.
 * Encapsulates all /v1/cashflow/* endpoints.
 * Components call these via hooks — never apiClient directly.
 */
import apiClient from './apiClient';

export const cashflowApi = {
  /**
   * Get a cash flow forecast.
   *
   * @param {Object} params
   * @param {string}  [params.account_id]       - plaid_account_id or omit for all
   * @param {number}  [params.horizon_days]     - 7, 14, or 30 (default 7)
   * @param {number}  [params.starting_balance] - current balance from Plaid
   */
  async getForecast(params = {}) {
    const query = {};
    if (params.account_id && params.account_id !== 'all') {
      query.account_id = params.account_id;
    }
    if (params.horizon_days) {
      query.horizon_days = params.horizon_days;
    }
    if (params.starting_balance !== undefined && params.starting_balance !== null) {
      query.starting_balance = params.starting_balance;
    }
    const res = await apiClient.get('/v1/cashflow/forecast', { params: query });
    return res.data;
  },
};
