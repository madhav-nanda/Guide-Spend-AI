/**
 * useWeeklyInsights — fetch weekly financial intelligence report.
 *
 * Reads selectedAccountId from AccountContext.
 * Auto-fetches on mount and whenever the account filter changes.
 * Includes race-condition protection via request ID tracking.
 *
 * Returns: { data, loading, error, refresh }
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAccount } from '../context/AccountContext';
import { insightsApi } from '../api/insightsApi';

export function useWeeklyInsights() {
  const { selectedAccountId } = useAccount();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Track the latest request to prevent stale responses from overwriting fresh data
  const requestIdRef = useRef(0);

  const fetchInsights = useCallback(async (accountId) => {
    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);

    try {
      const result = await insightsApi.getWeeklyInsights(accountId);

      // Only update state if this is still the latest request
      if (currentRequestId === requestIdRef.current) {
        setData(result);
      }
    } catch (err) {
      if (currentRequestId === requestIdRef.current) {
        setError(err.message || 'Failed to load weekly insights');
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, []);

  // Auto-fetch when account selection changes
  useEffect(() => {
    fetchInsights(selectedAccountId);
  }, [selectedAccountId, fetchInsights]);

  // Manual refresh (uses current account selection)
  const refresh = useCallback(() => {
    fetchInsights(selectedAccountId);
  }, [selectedAccountId, fetchInsights]);

  return { data, loading, error, refresh };
}
