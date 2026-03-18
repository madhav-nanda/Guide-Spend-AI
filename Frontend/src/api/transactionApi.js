/**
 * Transaction domain API.
 * Encapsulates GET /transactions (paginated + filterable), POST, DELETE.
 * Returns clean objects — callers never parse axios responses.
 */
import apiClient from './apiClient';

export const transactionApi = {
  /**
   * Fetch paginated transactions with optional account filter.
   * @param {{ page?: number, per_page?: number, account_id?: string }} params
   * @returns {{ transactions: Array, pagination: { page, per_page, total, total_pages } }}
   */
  async getTransactions({ page = 1, per_page = 50, account_id } = {}) {
    const params = { page, per_page };
    if (account_id && account_id !== 'all') {
      params.account_id = account_id;
    }
    const res = await apiClient.get('/transactions', { params });
    return res.data;
  },

  /**
   * Create a manual transaction.
   * @returns {{ message: string, id: number }}
   */
  async create({ amount, category, description, date }) {
    const res = await apiClient.post('/transactions', {
      amount,
      category,
      description,
      date,
    });
    return res.data;
  },

  /**
   * Delete a transaction by ID.
   * @returns {{ message: string }}
   */
  async delete(transactionId) {
    const res = await apiClient.delete(`/transactions/${transactionId}`);
    return res.data;
  },
};
