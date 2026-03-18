/**
 * useHealthScore — hook for the Financial Health Score engine.
 *
 * Reads selectedAccountId from AccountContext automatically.
 * Accepts a starting balance to factor into the cash buffer calculation.
 * Race-condition safe via request ID counter.
 *
 * Returns:
 *   {
 *     healthScore, loading, error, refresh,
 *     windowDays, setWindowDays,
 *   }
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAccount } from '../context/AccountContext';
import { healthScoreApi } from '../api/healthScoreApi';

const VALID_WINDOWS = [30, 60, 90];

export function useHealthScore(currentBalance = null) {
  const { selectedAccountId } = useAccount();

  const [healthScore, setHealthScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [windowDays, setWindowDaysState] = useState(90);

  const requestIdRef = useRef(0);

  const setWindowDays = useCallback((days) => {
    if (VALID_WINDOWS.includes(days)) {
      setWindowDaysState(days);
      setHealthScore(null); // Clear stale data
    }
  }, []);

  // ── Fetch health score ──
  const fetchHealthScore = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);

    try {
      const result = await healthScoreApi.getHealthScore({
        account_id: selectedAccountId,
        window_days: windowDays,
        current_balance: currentBalance,
      });
      if (currentRequestId === requestIdRef.current) {
        setHealthScore(result);
      }
    } catch (err) {
      if (currentRequestId === requestIdRef.current) {
        setError(err.message || 'Failed to load health score');
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [selectedAccountId, windowDays, currentBalance]);

  // ── Auto-fetch when params change ──
  useEffect(() => {
    fetchHealthScore();
  }, [fetchHealthScore]);

  return {
    healthScore,
    loading,
    error,
    refresh: fetchHealthScore,
    windowDays,
    setWindowDays,
  };
}
