/**
 * useAccounts — fetch and manage linked bank accounts.
 * Wraps plaidApi.getAccounts with loading, error, and refresh.
 */
import { useState, useCallback } from 'react';
import { plaidApi } from '../api/plaidApi';

export function useAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await plaidApi.getAccounts();
      setAccounts(data);
    } catch (err) {
      setError(err.message || 'Failed to load accounts');
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const validAccounts = accounts.filter((a) => !a.error);

  return { accounts, validAccounts, loading, error, fetchAccounts };
}
