/**
 * WeeklyInsights — renders the weekly financial intelligence card.
 *
 * Accepts pre-fetched data from the parent (via useWeeklyInsights hook).
 * Pure presentation: no API calls, no context reads.
 *
 * Layout:
 *   Top row:    Total Spent | WoW Change | Volatility Badge
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

function formatWeekRange(start, end) {
  if (!start || !end) return '';
  const opts = { month: 'short', day: 'numeric' };
  const s = new Date(start + 'T00:00:00');
  const e = new Date(end + 'T00:00:00');
  return `${s.toLocaleDateString('en-US', opts)} – ${e.toLocaleDateString('en-US', opts)}`;
}

const VOLATILITY_CONFIG = {
  low: { label: 'Low', color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' },
  medium: { label: 'Medium', color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20' },
  high: { label: 'High', color: 'text-rose-400', bg: 'bg-rose-400/10', border: 'border-rose-400/20' },
};

// ──────────────────────────────────────────────
// Skeleton Loader
// ──────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl">
      <div className="animate-pulse space-y-4">
        {/* Title skeleton */}
        <div className="h-3 w-32 bg-white/10 rounded" />

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
          <p className="text-sm font-medium text-white">Unable to load weekly insights</p>
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
// Main Component
// ──────────────────────────────────────────────

export default function WeeklyInsights({ data, loading, error, onRetry }) {
  // Loading state
  if (loading && !data) {
    return <SkeletonCard />;
  }

  // Error state (non-breaking — shows fallback, dashboard keeps working)
  if (error && !data) {
    return <ErrorFallback error={error} onRetry={onRetry} />;
  }

  // No data yet (shouldn't happen, but safe fallback)
  if (!data) {
    return null;
  }

  const {
    week_start,
    week_end,
    total_spent = 0,
    week_over_week_change = 0,
    volatility_score = 0,
    top_merchants = [],
    top_categories = [],
    explanation = {},
  } = data;

  const volLevel = explanation.volatility_level || 'low';
  const volConfig = VOLATILITY_CONFIG[volLevel] || VOLATILITY_CONFIG.low;

  // WoW direction: positive = spending increased (bad), negative = spending decreased (good)
  const wowIsGood = week_over_week_change <= 0;
  const WowIcon = week_over_week_change < 0 ? TrendingDown : week_over_week_change > 0 ? TrendingUp : Minus;
  const wowColor = week_over_week_change === 0
    ? 'text-slate-400'
    : wowIsGood
      ? 'text-emerald-400'
      : 'text-rose-400';

  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-white">Weekly Financial Insight</h4>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {formatWeekRange(week_start, week_end)}
          </p>
        </div>
        {/* Refresh indicator when reloading with existing data */}
        {loading && data && (
          <svg className="w-4 h-4 animate-spin text-slate-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
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

        {/* Week-over-Week Change */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            vs. Last Week
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <WowIcon className={`w-5 h-5 ${wowColor}`} />
            <span className={`text-xl font-extrabold ${wowColor}`}>
              {week_over_week_change > 0 ? '+' : ''}
              {week_over_week_change.toFixed(1)}%
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
          <p className={`text-xs font-medium ${wowColor}`}>
            {explanation.spending_change}
          </p>
        )}
      </div>
    </div>
  );
}
