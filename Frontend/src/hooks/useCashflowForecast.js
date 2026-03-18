/**
 * useCashflowForecast — hook for cash flow projections + overdraft risk.
 *
 * Reads selectedAccountId from AccountContext automatically.
 * Accepts a starting balance (from Plaid account data) to feed the forecast.
 * Race-condition safe via request ID counter.
 *
 * Returns:
 *   {
 *     forecast, loading, error, refresh,
 *     horizonDays, setHorizonDays,
 *   }
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAccount } from '../context/AccountContext';
import { cashflowApi } from '../api/cashflowApi';

const VALID_HORIZONS = [7, 14, 30];

export function useCashflowForecast(startingBalance = null) {
  const { selectedAccountId } = useAccount();

  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [horizonDays, setHorizonDaysState] = useState(7);

  const requestIdRef = useRef(0);

  const setHorizonDays = useCallback((days) => {
    if (VALID_HORIZONS.includes(days)) {
      setHorizonDaysState(days);
      setForecast(null); // Clear stale data
    }
  }, []);

  // ── Fetch forecast ──
  const fetchForecast = useCallback(async () => {
    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);

    try {
      const result = await cashflowApi.getForecast({
        account_id: selectedAccountId,
        horizon_days: horizonDays,
        starting_balance: startingBalance,
      });
      if (currentRequestId === requestIdRef.current) {
        setForecast(result);
      }
    } catch (err) {
      if (currentRequestId === requestIdRef.current) {
        setError(err.message || 'Failed to load forecast');
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [selectedAccountId, horizonDays, startingBalance]);

  // ── Auto-fetch when params change ──
  useEffect(() => {
    fetchForecast();
  }, [fetchForecast]);

  return {
    forecast,
    loading,
    error,
    refresh: fetchForecast,
    horizonDays,
    setHorizonDays,
  };
}
