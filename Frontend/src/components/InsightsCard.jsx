/**
 * InsightsCard — generalized financial intelligence card.
 *
 * Supports week, month, rolling, and custom time-range navigation.
 * Pure presentation: all state lives in the useTimeRangeInsights hook.
 *
 * Layout:
 *   Header:     Title + Mode tabs (Week | Month | Rolling | Custom)
 *   Nav row:    Period navigation (arrows, dropdown, or date picker)
 *   Top row:    Total Spent | Period Change | Volatility Badge
 *   Middle row: Biggest Merchant | Largest Category
 *   Bottom:     Summary + Spending Change message
 */
import {
  TrendingDown,
  TrendingUp,
  Minus,
  Activity,
  ShoppingBag,
  Tag,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Calendar,
  RefreshCw,
} from 'lucide-react';

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

function formatCurrency(amount) {
  if (amount == null) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDateRange(start, end) {
  if (!start || !end) return '';
  const s = new Date(start + 'T00:00:00');
  const e = new Date(end + 'T00:00:00');
  const sameYear = s.getFullYear() === e.getFullYear();

  const baseOpts = { month: 'short', day: 'numeric' };
  const withYear = { month: 'short', day: 'numeric', year: 'numeric' };

  if (sameYear) {
    return `${s.toLocaleDateString('en-US', baseOpts)} – ${e.toLocaleDateString('en-US', withYear)}`;
  }
  return `${s.toLocaleDateString('en-US', withYear)} – ${e.toLocaleDateString('en-US', withYear)}`;
}

const VOLATILITY_CONFIG = {
  low: { label: 'Low', color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' },
  medium: { label: 'Medium', color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20' },
  high: { label: 'High', color: 'text-rose-400', bg: 'bg-rose-400/10', border: 'border-rose-400/20' },
};

const MODE_LABELS = {
  week: 'Week',
  month: 'Month',
  rolling: 'Rolling',
  custom: 'Custom',
};

const ROLLING_OPTIONS = [
  { value: 7, label: 'Last 7 Days' },
  { value: 30, label: 'Last 30 Days' },
  { value: 90, label: 'Last 90 Days' },
];

// ──────────────────────────────────────────────
// Skeleton Loader
// ──────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl">
      <div className="animate-pulse space-y-4">
        {/* Title + tabs skeleton */}
        <div className="flex items-center justify-between">
          <div className="h-3 w-36 bg-white/10 rounded" />
          <div className="flex gap-1">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-7 w-16 bg-white/10 rounded-lg" />
            ))}
          </div>
        </div>

        {/* Nav skeleton */}
        <div className="h-8 w-64 bg-white/10 rounded-lg mx-auto" />

        {/* Top row: 3 metric cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white/5 rounded-xl p-4 space-y-2">
              <div className="h-2.5 w-20 bg-white/10 rounded" />
              <div className="h-6 w-24 bg-white/10 rounded" />
            </div>
          ))}
        </div>

        {/* Middle row: 2 cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-white/5 rounded-xl p-4 space-y-2">
              <div className="h-2.5 w-24 bg-white/10 rounded" />
              <div className="h-4 w-36 bg-white/10 rounded" />
            </div>
          ))}
        </div>

        {/* Bottom text */}
        <div className="space-y-2 pt-1">
          <div className="h-3 w-full bg-white/10 rounded" />
          <div className="h-3 w-3/4 bg-white/10 rounded" />
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Error Fallback
// ──────────────────────────────────────────────

function ErrorFallback({ error, onRetry }) {
  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl bg-rose-400/10 flex items-center justify-center shrink-0">
          <AlertCircle className="w-5 h-5 text-rose-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white">Unable to load financial insights</p>
          <p className="text-xs text-slate-400 mt-1">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 text-xs font-medium text-teal-400 hover:text-teal-300 transition-colors cursor-pointer"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Mode Tabs
// ──────────────────────────────────────────────

function ModeTabs({ mode, setMode }) {
  return (
    <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1 border border-white/5">
      {Object.entries(MODE_LABELS).map(([key, label]) => (
        <button
          key={key}
          onClick={() => setMode(key)}
          className={`
            text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-all cursor-pointer
            ${mode === key
              ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
              : 'text-slate-400 hover:text-slate-300 hover:bg-white/5 border border-transparent'
            }
          `}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

// ──────────────────────────────────────────────
// Navigation Controls
// ──────────────────────────────────────────────

function WeekMonthNav({ data, prevPeriod, nextPeriod, canGoNext, goToToday, loading }) {
  const isAtToday = !canGoNext;

  return (
    <div className="flex items-center justify-center gap-3">
      <button
        onClick={prevPeriod}
        disabled={loading}
        className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>

      <div className="flex items-center gap-2 min-w-[180px] justify-center">
        <Calendar className="w-3.5 h-3.5 text-slate-500" />
        <span className="text-xs font-medium text-slate-300">
          {formatDateRange(data?.start_date, data?.end_date)}
        </span>
      </div>

      <button
        onClick={nextPeriod}
        disabled={!canGoNext || loading}
        className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
        title={!canGoNext ? 'Already at current period' : ''}
      >
        <ChevronRight className="w-4 h-4" />
      </button>

      {!isAtToday && (
        <button
          onClick={goToToday}
          disabled={loading}
          className="text-[11px] font-semibold px-3 py-1.5 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/30 hover:bg-teal-500/30 transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
        >
          Today
        </button>
      )}
    </div>
  );
}

function RollingNav({ rollingDays, setRollingDays, data, loading }) {
  return (
    <div className="flex items-center justify-center gap-3">
      <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1 border border-white/5">
        {ROLLING_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setRollingDays(opt.value)}
            disabled={loading}
            className={`
              text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-all cursor-pointer
              ${rollingDays === opt.value
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-300 hover:bg-white/5 border border-transparent'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {data?.start_date && (
        <span className="text-[10px] text-slate-500">
          {formatDateRange(data.start_date, data.end_date)}
        </span>
      )}
    </div>
  );
}

function CustomNav({ customStart, customEnd, setCustomRange, applyCustomRange, data, loading }) {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
      <div className="flex items-center gap-2">
        <input
          type="date"
          value={customStart}
          onChange={(e) => setCustomRange(e.target.value, customEnd)}
          disabled={loading}
          className="text-xs bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500/40 transition-all disabled:opacity-50 [color-scheme:dark]"
        />
        <span className="text-slate-500 text-xs">to</span>
        <input
          type="date"
          value={customEnd}
          onChange={(e) => setCustomRange(customStart, e.target.value)}
          disabled={loading}
          className="text-xs bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500/40 transition-all disabled:opacity-50 [color-scheme:dark]"
        />
        <button
          onClick={applyCustomRange}
          disabled={!customStart || !customEnd || loading}
          className="text-xs font-semibold px-4 py-1.5 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/30 hover:bg-teal-500/30 transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
        >
          Apply
        </button>
      </div>

      {data?.start_date && (
        <span className="text-[10px] text-slate-500">
          Showing: {formatDateRange(data.start_date, data.end_date)}
        </span>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────

export default function InsightsCard({
  data,
  loading,
  error,
  refresh,
  mode,
  setMode,
  prevPeriod,
  nextPeriod,
  canGoNext,
  goToToday,
  rollingDays,
  setRollingDays,
  customStart,
  customEnd,
  setCustomRange,
  applyCustomRange,
}) {
  // Loading state (no data yet)
  if (loading && !data) {
    return <SkeletonCard />;
  }

  // Error state (non-breaking)
  if (error && !data) {
    return <ErrorFallback error={error} onRetry={refresh} />;
  }

  // No data yet
  if (!data) {
    return null;
  }

  const {
    total_spent = 0,
    total_income = 0,
    period_change = 0,
    volatility_score = 0,
    explanation = {},
  } = data;

  const volLevel = explanation.volatility_level || 'low';
  const volConfig = VOLATILITY_CONFIG[volLevel] || VOLATILITY_CONFIG.low;

  // Period change direction
  const changeIsGood = period_change <= 0;
  const ChangeIcon = period_change < 0 ? TrendingDown : period_change > 0 ? TrendingUp : Minus;
  const changeColor = period_change === 0
    ? 'text-slate-400'
    : changeIsGood
      ? 'text-emerald-400'
      : 'text-rose-400';

  // Period label for the "vs." tile
  const vsLabel = mode === 'week'
    ? 'vs. Prev Week'
    : mode === 'month'
      ? 'vs. Prev Month'
      : 'vs. Prev Period';

  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl space-y-5">
      {/* ── Header: Title + Mode Tabs ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <h4 className="text-sm font-semibold text-white">Financial Insights</h4>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {data.granularity === 'week' && 'Weekly overview'}
              {data.granularity === 'month' && 'Monthly overview'}
              {data.granularity === 'rolling' && `Rolling ${(new Date(data.end_date + 'T00:00:00') - new Date(data.start_date + 'T00:00:00')) / 86400000 + 1}-day overview`}
              {data.granularity === 'custom' && 'Custom range overview'}
            </p>
          </div>

          {/* Refresh indicator when reloading with existing data */}
          {loading && data && (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
          )}
        </div>

        <ModeTabs mode={mode} setMode={setMode} />
      </div>

      {/* ── Navigation Controls ── */}
      <div className="border-t border-white/5 pt-4">
        {(mode === 'week' || mode === 'month') && (
          <WeekMonthNav
            data={data}
            prevPeriod={prevPeriod}
            nextPeriod={nextPeriod}
            canGoNext={canGoNext}
            goToToday={goToToday}
            loading={loading}
          />
        )}
        {mode === 'rolling' && (
          <RollingNav
            rollingDays={rollingDays}
            setRollingDays={setRollingDays}
            data={data}
            loading={loading}
          />
        )}
        {mode === 'custom' && (
          <CustomNav
            customStart={customStart}
            customEnd={customEnd}
            setCustomRange={setCustomRange}
            applyCustomRange={applyCustomRange}
            data={data}
            loading={loading}
          />
        )}
      </div>

      {/* ── Top Row: 3 Metric Tiles ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Total Spent */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Total Spent
          </p>
          <p className="text-xl font-extrabold text-white mt-1.5">
            {formatCurrency(total_spent)}
          </p>
        </div>

        {/* Period Change */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            {vsLabel}
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <ChangeIcon className={`w-5 h-5 ${changeColor}`} />
            <span className={`text-xl font-extrabold ${changeColor}`}>
              {period_change > 0 ? '+' : ''}
              {period_change.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Volatility Badge */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Spending Volatility
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <Activity className={`w-5 h-5 ${volConfig.color}`} />
            <span
              className={`inline-flex items-center text-xs font-bold px-2.5 py-1 rounded-lg ${volConfig.bg} ${volConfig.color} ${volConfig.border} border`}
            >
              {volConfig.label}
            </span>
            <span className="text-xs text-slate-500">{volatility_score.toFixed(0)}/100</span>
          </div>
        </div>
      </div>

      {/* ── Middle Row: Merchant + Category ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Biggest Merchant */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5 flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center shrink-0">
            <ShoppingBag className="w-4 h-4 text-blue-400" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Biggest Merchant
            </p>
            <p className="text-sm font-semibold text-white mt-1 truncate">
              {explanation.biggest_merchant || 'No data'}
            </p>
          </div>
        </div>

        {/* Largest Category */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5 flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-violet-400/10 flex items-center justify-center shrink-0">
            <Tag className="w-4 h-4 text-violet-400" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Largest Category
            </p>
            <p className="text-sm font-semibold text-white mt-1 truncate">
              {explanation.largest_category || 'No data'}
            </p>
          </div>
        </div>
      </div>

      {/* ── Bottom: Summary + Spending Change ── */}
      <div className="border-t border-white/5 pt-4 space-y-2">
        {explanation.summary && (
          <p className="text-sm text-slate-300 leading-relaxed">
            {explanation.summary}
          </p>
        )}
        {explanation.spending_change && (
          <p className={`text-xs font-medium ${changeColor}`}>
            {explanation.spending_change}
          </p>
        )}
      </div>
    </div>
  );
}
