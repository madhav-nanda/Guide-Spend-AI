/**
 * Plaid domain API.
 * Encapsulates link token, exchange, sync, accounts, disconnect.
 * No component should import apiClient for Plaid calls.
 */
import apiClient from './apiClient';

export const plaidApi = {
  /**
   * Generate a Plaid Link token.
   * @returns {{ link_token: string }}
   */
  async createLinkToken() {
    const res = await apiClient.post('/plaid/create_link_token');
    return res.data;
  },

  /**
   * Exchange a public token for an access token and store it.
   * @returns {{ message: string, item_id: string, institution_name: string }}
   */
  async exchangeToken(publicToken, institutionId, institutionName) {
    const res = await apiClient.post('/plaid/exchange_token', {
      public_token: publicToken,
      institution_id: institutionId,
      institution_name: institutionName,
    });
    return res.data;
  },

  /**
   * Trigger incremental transaction sync.
   * @returns {{ message: string, added: number, modified: number, removed: number }}
   */
  async syncTransactions() {
    const res = await apiClient.post('/plaid/sync_transactions');
    return res.data;
  },

  /**
   * Fetch all linked accounts with real-time balances.
   * @returns {Array} accounts
   */
  async getAccounts() {
    const res = await apiClient.get('/plaid/accounts');
    return res.data.accounts || [];
  },

  /**
   * Disconnect a linked bank account.
   * @param {string} itemId - Plaid item_id
   * @returns {{ message: string, transactions_removed: number }}
   */
  async disconnect(itemId) {
    const res = await apiClient.delete(`/plaid/disconnect/${itemId}`);
    return res.data;
  },
};
