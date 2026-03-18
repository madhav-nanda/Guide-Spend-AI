/**
 * useTransactions — paginated transaction fetching.
 *
 * Reads the selected account from AccountContext.
 * Exposes page controls (next, prev, goToPage) and pagination metadata.
 * Components render data + controls — zero fetch logic in JSX.
 */
import { useState, useCallback } from 'react';
import { transactionApi } from '../api/transactionApi';

const DEFAULT_PER_PAGE = 50;

export function useTransactions() {
  const [transactions, setTransactions] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: DEFAULT_PER_PAGE,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTransactions = useCallback(
    async ({ page = 1, per_page = DEFAULT_PER_PAGE, account_id } = {}) => {
      setLoading(true);
      setError(null);
      try {
        const data = await transactionApi.getTransactions({
          page,
          per_page,
          account_id,
        });
        setTransactions(data.transactions || []);
        setPagination(
          data.pagination || {
            page,
            per_page,
            total: (data.transactions || []).length,
            total_pages: 1,
          }
        );
      } catch (err) {
        setError(err.message || 'Failed to load transactions');
        setTransactions([]);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const nextPage = useCallback(
    (accountId) => {
      if (pagination.page < pagination.total_pages) {
        fetchTransactions({
          page: pagination.page + 1,
          per_page: pagination.per_page,
          account_id: accountId,
        });
      }
    },
    [pagination, fetchTransactions]
  );

  const prevPage = useCallback(
    (accountId) => {
      if (pagination.page > 1) {
        fetchTransactions({
          page: pagination.page - 1,
          per_page: pagination.per_page,
          account_id: accountId,
        });
      }
    },
    [pagination, fetchTransactions]
  );

  const goToPage = useCallback(
    (pageNum, accountId) => {
      fetchTransactions({
        page: pageNum,
        per_page: pagination.per_page,
        account_id: accountId,
      });
    },
    [pagination.per_page, fetchTransactions]
  );

  return {
    transactions,
    pagination,
    loading,
    error,
    fetchTransactions,
    nextPage,
    prevPage,
    goToPage,
  };
}
