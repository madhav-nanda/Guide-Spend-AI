/**
 * useTimeRangeInsights — generalized financial insights hook.
 *
 * Supports week, month, rolling, and custom date range navigation.
 * Reads selectedAccountId from AccountContext automatically.
 * Race-condition safe via request ID counter.
 * Persists the selected mode to localStorage.
 *
 * Returns:
 *   {
 *     data, loading, error, refresh,
 *     mode, setMode,
 *     offset, prevPeriod, nextPeriod,
 *     rollingDays, setRollingDays,
 *     customStart, customEnd, setCustomRange, applyCustomRange,
 *     canGoNext,
 *   }
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useAccount } from '../context/AccountContext';
import { insightsApi } from '../api/insightsApi';

const STORAGE_KEY = 'guidespend_insights_mode';

const VALID_MODES = ['week', 'month', 'rolling', 'custom'];

function loadPersistedMode() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return VALID_MODES.includes(saved) ? saved : 'week';
  } catch {
    return 'week';
  }
}

export function useTimeRangeInsights() {
  const { selectedAccountId } = useAccount();

  // ── Navigation state ──
  const [mode, setModeState] = useState(loadPersistedMode);
  const [offset, setOffset] = useState(0);
  const [rollingDays, setRollingDaysState] = useState(30);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [customApplied, setCustomApplied] = useState(false);

  // ── Data state ──
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ── Race-condition protection ──
  const requestIdRef = useRef(0);

  // ── Mode setter: reset offset, clear stale data, persist ──
  const setMode = useCallback((newMode) => {
    if (!VALID_MODES.includes(newMode)) return;
    setModeState(newMode);
    setOffset(0);
    setCustomApplied(false);
    setData(null);
    try {
      localStorage.setItem(STORAGE_KEY, newMode);
    } catch { /* quota exceeded — ignore */ }
  }, []);

  // ── Rolling days setter ──
  const setRollingDays = useCallback((days) => {
    setRollingDaysState(days);
  }, []);

  // ── Custom range setters ──
  const setCustomRange = useCallback((start, end) => {
    setCustomStart(start);
    setCustomEnd(end);
  }, []);

  const applyCustomRange = useCallback(() => {
    if (customStart && customEnd) {
      setCustomApplied(true);
    }
  }, [customStart, customEnd]);

  // ── Navigation ──
  const prevPeriod = useCallback(() => {
    setOffset((o) => o - 1);
  }, []);

  const nextPeriod = useCallback(() => {
    setOffset((o) => o + 1);
  }, []);

  // ── Go to today (reset offset to 0) ──
  const goToToday = useCallback(() => {
    setOffset(0);
  }, []);

  // ── Can go next? (offset < 0 means we're in the past) ──
  const canGoNext = offset < 0;

  // ── Build query params from current state ──
  const queryParams = useMemo(() => {
    const params = { type: mode };

    if (mode === 'week' || mode === 'month') {
      params.offset = offset;
    } else if (mode === 'rolling') {
      params.days = rollingDays;
    } else if (mode === 'custom' && customApplied) {
      params.start = customStart;
      params.end = customEnd;
    }

    if (selectedAccountId && selectedAccountId !== 'all') {
      params.account_id = selectedAccountId;
    }

    return params;
  }, [mode, offset, rollingDays, customStart, customEnd, customApplied, selectedAccountId]);

  // ── Determine if we should fetch ──
  const shouldFetch = mode !== 'custom' || customApplied;

  // ── Fetch ──
  const fetchInsights = useCallback(async (params) => {
    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);

    try {
      const result = await insightsApi.getTimeRangeInsights(params);
      if (currentRequestId === requestIdRef.current) {
        setData(result);
      }
    } catch (err) {
      if (currentRequestId === requestIdRef.current) {
        setError(err.message || 'Failed to load insights');
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, []);

  // ── Auto-fetch when params change ──
  useEffect(() => {
    if (shouldFetch) {
      fetchInsights(queryParams);
    }
  }, [queryParams, shouldFetch, fetchInsights]);

  // ── Manual refresh ──
  const refresh = useCallback(() => {
    if (shouldFetch) {
      fetchInsights(queryParams);
    }
  }, [queryParams, shouldFetch, fetchInsights]);

  return {
    // Data
    data,
    loading,
    error,
    refresh,

    // Mode
    mode,
    setMode,

    // Week/Month navigation
    offset,
    prevPeriod,
    nextPeriod,
    canGoNext,
    goToToday,

    // Rolling
    rollingDays,
    setRollingDays,

    // Custom
    customStart,
    customEnd,
    setCustomRange,
    applyCustomRange,
  };
}
