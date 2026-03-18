/**
 * CashflowCard — cash flow forecast + overdraft risk UI.
 *
 * Shows:
 *   - Risk score badge (Low/Medium/High)
 *   - Projected end balance + min balance
 *   - Horizon selector (7 / 14 / 30 days)
 *   - Daily balance mini-chart (sparkline via CSS bars)
 *   - Upcoming subscriptions factored in
 *   - Explanation summary
 *
 * Matches the InsightsCard design language (glassmorphism, slate/teal).
 */
import {
  RefreshCw,
  AlertCircle,
  TrendingDown,
  TrendingUp,
  Shield,
  ShieldAlert,
  ShieldOff,
  Activity,
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

const RISK_CONFIG = {
  low:    { label: 'Low Risk',    color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20', Icon: Shield },
  medium: { label: 'Medium Risk', color: 'text-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-400/20',   Icon: ShieldAlert },
  high:   { label: 'High Risk',   color: 'text-rose-400',    bg: 'bg-rose-400/10',    border: 'border-rose-400/20',    Icon: ShieldOff },
};

const HORIZON_OPTIONS = [
  { value: 7,  label: '7 Days' },
  { value: 14, label: '14 Days' },
  { value: 30, label: '30 Days' },
];

// ──────────────────────────────────────────────
// Skeleton Loader
// ──────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl">
      <div className="animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-3 w-40 bg-white/10 rounded" />
          <div className="flex gap-1">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-7 w-16 bg-white/10 rounded-lg" />
            ))}
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white/5 rounded-xl p-4 space-y-2">
              <div className="h-2.5 w-20 bg-white/10 rounded" />
              <div className="h-6 w-24 bg-white/10 rounded" />
            </div>
          ))}
        </div>
        <div className="h-16 bg-white/5 rounded-xl" />
        <div className="h-3 w-3/4 bg-white/10 rounded" />
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
          <p className="text-sm font-medium text-white">Unable to load forecast</p>
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
// Balance Sparkline (CSS bars)
// ──────────────────────────────────────────────

function BalanceSparkline({ dailyBalances }) {
  if (!dailyBalances || dailyBalances.length === 0) return null;

  const balances = dailyBalances.map((d) => d.projected_balance);
  const max = Math.max(...balances, 1);
  const min = Math.min(...balances, 0);
  const range = max - min || 1;

  return (
    <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Projected Balance
      </p>
      <div className="flex items-end gap-[2px] h-12">
        {dailyBalances.map((d, i) => {
          const pct = Math.max(5, ((d.projected_balance - min) / range) * 100);
          const isNegative = d.projected_balance < 0;
          return (
            <div
              key={i}
              className="flex-1 group relative"
              title={`${formatDate(d.date)}: ${formatCurrency(d.projected_balance)}`}
            >
              <div
                className={`rounded-t-sm transition-all ${
                  isNegative ? 'bg-rose-400/60' : 'bg-teal-400/40 group-hover:bg-teal-400/70'
                }`}
                style={{ height: `${pct}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex justify-between mt-1.5">
        <span className="text-[9px] text-slate-600">
          {formatDate(dailyBalances[0]?.date)}
        </span>
        <span className="text-[9px] text-slate-600">
          {formatDate(dailyBalances[dailyBalances.length - 1]?.date)}
        </span>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Horizon Tabs
// ──────────────────────────────────────────────

function HorizonTabs({ horizonDays, setHorizonDays, loading }) {
  return (
    <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1 border border-white/5">
      {HORIZON_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => setHorizonDays(opt.value)}
          disabled={loading}
          className={`
            text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-all cursor-pointer
            ${horizonDays === opt.value
              ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
              : 'text-slate-400 hover:text-slate-300 hover:bg-white/5 border border-transparent'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────

export default function CashflowCard({
  forecast,
  loading,
  error,
  refresh,
  horizonDays,
  setHorizonDays,
}) {
  // Loading state (no data yet)
  if (loading && !forecast) {
    return <SkeletonCard />;
  }

  // Error state
  if (error && !forecast) {
    return <ErrorFallback error={error} onRetry={refresh} />;
  }

  // No data yet
  if (!forecast) {
    return null;
  }

  const {
    starting_balance = 0,
    projected_end_balance = 0,
    min_projected_balance = 0,
    risk_score = 0,
    projected_daily_balances = [],
    drivers_json = {},
    explanation_json = {},
  } = forecast;

  const riskLevel = explanation_json.risk_level || 'low';
  const riskConfig = RISK_CONFIG[riskLevel] || RISK_CONFIG.low;
  const RiskIcon = riskConfig.Icon;

  const balanceChange = projected_end_balance - starting_balance;
  const isPositiveChange = balanceChange >= 0;

  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl space-y-5">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <h4 className="text-sm font-semibold text-white">Cash Flow Forecast</h4>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {horizonDays}-day projection
            </p>
          </div>
          {loading && forecast && (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
          )}
        </div>

        <HorizonTabs
          horizonDays={horizonDays}
          setHorizonDays={setHorizonDays}
          loading={loading}
        />
      </div>

      {/* ── Top Metrics ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Risk Score */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Overdraft Risk
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <RiskIcon className={`w-5 h-5 ${riskConfig.color}`} />
            <span
              className={`inline-flex items-center text-xs font-bold px-2.5 py-1 rounded-lg ${riskConfig.bg} ${riskConfig.color} ${riskConfig.border} border`}
            >
              {riskConfig.label}
            </span>
            <span className="text-xs text-slate-500">{Math.round(risk_score)}/100</span>
          </div>
        </div>

        {/* Projected End Balance */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Projected Balance
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            {isPositiveChange
              ? <TrendingUp className="w-4 h-4 text-emerald-400" />
              : <TrendingDown className="w-4 h-4 text-rose-400" />
            }
            <span className={`text-xl font-extrabold ${projected_end_balance < 0 ? 'text-rose-400' : 'text-white'}`}>
              {formatCurrency(projected_end_balance)}
            </span>
          </div>
        </div>

        {/* Minimum Balance */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Lowest Balance
          </p>
          <p className={`text-xl font-extrabold mt-1.5 ${min_projected_balance < 0 ? 'text-rose-400' : min_projected_balance < 50 ? 'text-amber-400' : 'text-white'}`}>
            {formatCurrency(min_projected_balance)}
          </p>
          {explanation_json.min_balance_date && (
            <p className="text-[10px] text-slate-500 mt-0.5">
              on {formatDate(explanation_json.min_balance_date)}
            </p>
          )}
        </div>
      </div>

      {/* ── Balance Sparkline ── */}
      <BalanceSparkline dailyBalances={projected_daily_balances} />

      {/* ── Drivers: Daily Averages + Subscriptions ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Daily averages */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Daily Averages
          </p>
          <div className="flex items-center gap-4 mt-2">
            <div>
              <p className="text-xs text-slate-500">Spend</p>
              <p className="text-sm font-bold text-rose-400">
                {formatCurrency(drivers_json.daily_spend_avg)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Income</p>
              <p className="text-sm font-bold text-emerald-400">
                {formatCurrency(drivers_json.daily_income_avg)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Volatility</p>
              <p className="text-sm font-bold text-slate-300">
                {Math.round(drivers_json.volatility || 0)}/100
              </p>
            </div>
          </div>
        </div>

        {/* Upcoming subscriptions */}
        <div className="bg-white/[0.03] rounded-xl p-4 border border-white/5">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Upcoming Subscriptions
          </p>
          {(drivers_json.upcoming_subscriptions || []).length > 0 ? (
            <div className="mt-2 space-y-1">
              {(drivers_json.upcoming_subscriptions || []).slice(0, 3).map((sub, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 truncate">{sub.merchant}</span>
                  <span className="text-rose-400 font-medium shrink-0 ml-2">
                    {formatCurrency(sub.amount)}
                  </span>
                </div>
              ))}
              {(drivers_json.upcoming_subscriptions || []).length > 3 && (
                <p className="text-[10px] text-slate-500">
                  +{drivers_json.upcoming_subscriptions.length - 3} more
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500 mt-2">No upcoming charges detected</p>
          )}
        </div>
      </div>

      {/* ── Summary ── */}
      {explanation_json.summary && (
        <div className="border-t border-white/5 pt-4 space-y-2">
          <p className="text-sm text-slate-300 leading-relaxed">
            {explanation_json.summary}
          </p>
          {explanation_json.risk_rationale && (
            <p className={`text-xs font-medium ${riskConfig.color}`}>
              {explanation_json.risk_rationale}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
