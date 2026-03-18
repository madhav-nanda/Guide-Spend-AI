/**
 * SubscriptionsCard — detected recurring payments UI.
 *
 * Shows a list of detected subscriptions with:
 *   - Merchant name + cadence badge
 *   - Average amount + next expected date
 *   - Confidence indicator
 *   - Recompute button
 *
 * Matches the InsightsCard design language (glassmorphism, slate/teal).
 */
import {
  RefreshCw,
  AlertCircle,
  Repeat,
  Calendar,
  DollarSign,
  ChevronRight,
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

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const target = new Date(dateStr + 'T00:00:00');
  const diff = Math.ceil((target - now) / 86400000);
  return diff;
}

const CADENCE_CONFIG = {
  weekly:    { label: 'Weekly',    color: 'text-blue-400',    bg: 'bg-blue-400/10',    border: 'border-blue-400/20' },
  biweekly:  { label: 'Biweekly', color: 'text-cyan-400',    bg: 'bg-cyan-400/10',    border: 'border-cyan-400/20' },
  monthly:   { label: 'Monthly',  color: 'text-teal-400',    bg: 'bg-teal-400/10',    border: 'border-teal-400/20' },
  quarterly: { label: 'Quarterly',color: 'text-violet-400',  bg: 'bg-violet-400/10',  border: 'border-violet-400/20' },
};

function confidenceColor(score) {
  if (score >= 70) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  return 'text-slate-500';
}

// ──────────────────────────────────────────────
// Skeleton Loader
// ──────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl">
      <div className="animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-3 w-40 bg-white/10 rounded" />
          <div className="h-7 w-20 bg-white/10 rounded-lg" />
        </div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/5 rounded-xl p-4 space-y-2">
            <div className="h-3 w-32 bg-white/10 rounded" />
            <div className="h-4 w-20 bg-white/10 rounded" />
          </div>
        ))}
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
          <p className="text-sm font-medium text-white">Unable to load subscriptions</p>
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
// Subscription Row
// ──────────────────────────────────────────────

function SubscriptionRow({ sub }) {
  const cadence = CADENCE_CONFIG[sub.cadence] || CADENCE_CONFIG.monthly;
  const days = daysUntil(sub.next_expected_date);
  const daysLabel = days !== null
    ? days === 0 ? 'Today'
      : days === 1 ? 'Tomorrow'
        : days < 0 ? `${Math.abs(days)}d overdue`
          : `in ${days}d`
    : '';

  return (
    <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5 hover:bg-white/[0.05] transition-all">
      <div className="flex items-center justify-between gap-3">
        {/* Left: icon + merchant info */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="w-9 h-9 rounded-lg bg-teal-400/10 flex items-center justify-center shrink-0">
            <Repeat className="w-4 h-4 text-teal-400" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-white truncate">
                {sub.merchant_display_name}
              </p>
              <span
                className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-md ${cadence.bg} ${cadence.color} ${cadence.border} border shrink-0`}
              >
                {cadence.label}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {formatDate(sub.next_expected_date)}
                {daysLabel && (
                  <span className={`ml-1 ${days !== null && days < 0 ? 'text-rose-400' : days <= 2 ? 'text-amber-400' : 'text-slate-500'}`}>
                    ({daysLabel})
                  </span>
                )}
              </span>
              <span className={`text-[10px] font-medium ${confidenceColor(sub.confidence_score)}`}>
                {Math.round(sub.confidence_score)}% confidence
              </span>
            </div>
          </div>
        </div>

        {/* Right: amount */}
        <div className="text-right shrink-0">
          <p className="text-sm font-bold text-white">
            {formatCurrency(sub.avg_amount)}
          </p>
          <p className="text-[10px] text-slate-500">avg/charge</p>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Empty State
// ──────────────────────────────────────────────

function EmptyState({ onRecompute, recomputing }) {
  return (
    <div className="text-center py-8 space-y-3">
      <Repeat className="w-8 h-8 text-slate-600 mx-auto" />
      <p className="text-sm text-slate-400">No recurring payments detected yet</p>
      <p className="text-xs text-slate-500">
        We need at least 3 similar transactions to detect a subscription pattern.
      </p>
      <button
        onClick={onRecompute}
        disabled={recomputing}
        className="text-xs font-semibold px-4 py-2 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/30 hover:bg-teal-500/30 transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
      >
        {recomputing ? 'Scanning...' : 'Scan for Subscriptions'}
      </button>
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────

export default function SubscriptionsCard({
  subscriptions,
  count,
  loading,
  error,
  refresh,
  recompute,
  recomputing,
}) {
  // Loading state (no data yet)
  if (loading && !subscriptions.length) {
    return <SkeletonCard />;
  }

  // Error state
  if (error && !subscriptions.length) {
    return <ErrorFallback error={error} onRetry={refresh} />;
  }

  // Compute monthly total
  const monthlyTotal = subscriptions.reduce((sum, s) => {
    const multiplier =
      s.cadence === 'weekly' ? 4.33
        : s.cadence === 'biweekly' ? 2.17
          : s.cadence === 'quarterly' ? 0.33
            : 1;
    return sum + (s.avg_amount || 0) * multiplier;
  }, 0);

  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl space-y-5">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h4 className="text-sm font-semibold text-white">Recurring Payments</h4>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {count} detected subscription{count !== 1 ? 's' : ''}
              {count > 0 && ` · ~${formatCurrency(monthlyTotal)}/mo`}
            </p>
          </div>
          {loading && subscriptions.length > 0 && (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
          )}
        </div>

        <button
          onClick={recompute}
          disabled={recomputing}
          className="inline-flex items-center gap-1.5 text-[11px] font-semibold px-3 py-1.5 rounded-lg bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10 hover:text-white transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-3 h-3 ${recomputing ? 'animate-spin' : ''}`} />
          {recomputing ? 'Scanning...' : 'Rescan'}
        </button>
      </div>

      {/* ── List or empty state ── */}
      {subscriptions.length === 0 ? (
        <EmptyState onRecompute={recompute} recomputing={recomputing} />
      ) : (
        <div className="space-y-2">
          {subscriptions.map((sub) => (
            <SubscriptionRow key={sub.id} sub={sub} />
          ))}
        </div>
      )}
    </div>
  );
}
