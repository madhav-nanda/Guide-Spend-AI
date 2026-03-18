/**
 * useSubscriptions — hook for detected recurring merchants / subscriptions.
 *
 * Reads selectedAccountId from AccountContext automatically.
 * Race-condition safe via request ID counter.
 *
 * Returns:
 *   {
 *     subscriptions, count, loading, error,
 *     refresh, recompute, recomputing,
 *   }
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAccount } from '../context/AccountContext';
import { subscriptionsApi } from '../api/subscriptionsApi';

export function useSubscriptions() {
  const { selectedAccountId } = useAccount();

  const [subscriptions, setSubscriptions] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recomputing, setRecomputing] = useState(false);

  const requestIdRef = useRef(0);

  // ── Fetch subscriptions ──
  const fetchSubscriptions = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);

    try {
      const result = await subscriptionsApi.getSubscriptions({
        account_id: selectedAccountId,
        min_confidence: 30,
      });
      if (currentRequestId === requestIdRef.current) {
        setSubscriptions(result.subscriptions || []);
        setCount(result.count || 0);
      }
    } catch (err) {
      if (currentRequestId === requestIdRef.current) {
        setError(err.message || 'Failed to load subscriptions');
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [selectedAccountId]);

  // ── Auto-fetch when account changes ──
  useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  // ── Recompute (trigger server-side detection) ──
  const recompute = useCallback(async () => {
    setRecomputing(true);
    try {
      await subscriptionsApi.recompute({
        account_id: selectedAccountId,
      });
      // Refresh the list after recompute
      await fetchSubscriptions();
    } catch (err) {
      setError(err.message || 'Failed to recompute subscriptions');
    } finally {
      setRecomputing(false);
    }
  }, [selectedAccountId, fetchSubscriptions]);

  return {
    subscriptions,
    count,
    loading,
    error,
    refresh: fetchSubscriptions,
    recompute,
    recomputing,
  };
}
