/**
 * Subscriptions domain API.
 * Encapsulates all /v1/subscriptions/* endpoints.
 * Components call these via hooks — never apiClient directly.
 */
import apiClient from './apiClient';

export const subscriptionsApi = {
  /**
   * List detected recurring merchants / subscriptions.
   *
   * @param {Object} params
   * @param {string}  [params.account_id]      - plaid_account_id or omit for all
   * @param {number}  [params.min_confidence]   - minimum confidence 0–100
   */
  async getSubscriptions(params = {}) {
    const query = {};
    if (params.account_id && params.account_id !== 'all') {
      query.account_id = params.account_id;
    }
    if (params.min_confidence !== undefined) {
      query.min_confidence = params.min_confidence;
    }
    const res = await apiClient.get('/v1/subscriptions', { params: query });
    return res.data;
  },

  /**
   * Get full details for a single subscription.
   *
   * @param {number} id - Subscription (recurring_merchant) ID
   */
  async getSubscriptionDetail(id) {
    const res = await apiClient.get(`/v1/subscriptions/${id}`);
    return res.data;
  },

  /**
   * Trigger subscription detection recompute for the current user.
   *
   * @param {Object} params
   * @param {string}  [params.account_id] - plaid_account_id or omit for all
   */
  async recompute(params = {}) {
    const query = {};
    if (params.account_id && params.account_id !== 'all') {
      query.account_id = params.account_id;
    }
    const res = await apiClient.post('/v1/subscriptions/recompute', null, { params: query });
    return res.data;
  },
};
