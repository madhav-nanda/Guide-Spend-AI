/**
 * Insights domain API.
 * Encapsulates all /v1/insights/* endpoints.
 * Components call these via hooks — never apiClient directly.
 */
import apiClient from './apiClient';

export const insightsApi = {
  /**
   * Fetch a time-range financial report.
   * Generates on-demand server-side if no cached report exists.
   *
   * @param {Object} params
   * @param {'week'|'month'|'rolling'|'custom'} params.type
   * @param {number}  [params.offset]     - week/month offset (0 = current)
   * @param {number}  [params.days]       - rolling day count (7, 30, 90)
   * @param {string}  [params.start]      - custom start YYYY-MM-DD
   * @param {string}  [params.end]        - custom end YYYY-MM-DD
   * @param {string}  [params.account_id] - plaid_account_id or omit for all
   */
  async getTimeRangeInsights(params = {}) {
    const query = { type: params.type || 'week' };

    if (params.offset !== undefined && params.offset !== null) {
      query.offset = params.offset;
    }
    if (params.days) query.days = params.days;
    if (params.start) query.start = params.start;
    if (params.end) query.end = params.end;
    if (params.account_id && params.account_id !== 'all') {
      query.account_id = params.account_id;
    }

    const res = await apiClient.get('/v1/insights/time-range', { params: query });
    return res.data;
  },

  /**
   * Legacy: Fetch current week report.
   * Kept for any code still using the old API shape.
   */
  async getWeeklyInsights(accountId) {
    const params = {};
    if (accountId && accountId !== 'all') {
      params.account_id = accountId;
    }
    const res = await apiClient.get('/v1/insights/weekly/latest', { params });
    return res.data;
  },
};
