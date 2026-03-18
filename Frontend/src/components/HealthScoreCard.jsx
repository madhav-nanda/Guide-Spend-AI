/**
 * HealthScoreCard — Financial Health Score gauge + breakdown UI.
 *
 * Shows:
 *   - Circular score gauge (0-100) with color scale
 *   - Four component score bars (Savings, Volatility, Subscriptions, Buffer)
 *   - Analysis window selector (30 / 60 / 90 days)
 *   - Explanation panel: summary, strengths, risks, suggestions
 *
 * Matches the InsightsCard design language (glassmorphism, slate/teal).
 */
import {
  RefreshCw,
  AlertCircle,
  Heart,
  PiggyBank,
  Activity,
  Repeat,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { useState } from 'react';

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

function scoreColor(score) {
  if (score >= 70) return { text: 'text-emerald-400', bg: 'bg-emerald-400', ring: 'stroke-emerald-400' };
  if (score >= 40) return { text: 'text-amber-400', bg: 'bg-amber-400', ring: 'stroke-amber-400' };
  return { text: 'text-rose-400', bg: 'bg-rose-400', ring: 'stroke-rose-400' };
}

function scoreLabel(score) {
  if (score >= 80) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 55) return 'Fair';
  if (score >= 40) return 'Needs Work';
  return 'At Risk';
}

const WINDOW_OPTIONS = [
  { value: 30, label: '30 Days' },
  { value: 60, label: '60 Days' },
  { value: 90, label: '90 Days' },
];

const COMPONENT_CONFIG = {
  savings:       { label: 'Savings Rate',    Icon: PiggyBank,  metricKey: 'savings_ratio',       format: (v) => `${(v * 100).toFixed(0)}%` },
  volatility:    { label: 'Spending Stability', Icon: Activity, metricKey: 'spending_volatility', format: (v) => v <= 0.3 ? 'Stable' : v <= 0.6 ? 'Moderate' : 'Volatile' },
  subscriptions: { label: 'Subscription Load',  Icon: Repeat,   metricKey: 'recurring_burden',    format: (v) => `${(v * 100).toFixed(0)}% of income` },
  cash_buffer:   { label: 'Cash Buffer',      Icon: ShieldCheck, metricKey: 'cash_buffer_days',   format: (v) => `${v.toFixed(0)} days` },
};

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
        <div className="flex justify-center">
          <div className="w-32 h-32 rounded-full bg-white/5 border-4 border-white/10" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white/5 rounded-xl p-3 space-y-2">
              <div className="h-2.5 w-20 bg-white/10 rounded" />
              <div className="h-4 w-full bg-white/10 rounded" />
            </div>
          ))}
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
          <p className="text-sm font-medium text-white">Unable to load health score</p>
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
// Score Gauge (SVG circle)
// ──────────────────────────────────────────────

function ScoreGauge({ score }) {
  const colors = scoreColor(score);
  const label = scoreLabel(score);
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const dashOffset = circumference - progress;

  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg className="w-36 h-36 -rotate-90" viewBox="0 0 120 120">
        {/* Background ring */}
        <circle
          cx="60" cy="60" r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="8"
        />
        {/* Progress ring */}
        <circle
          cx="60" cy="60" r={radius}
          fill="none"
          className={colors.ring}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-extrabold ${colors.text}`}>{score}</span>
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">
          {label}
        </span>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Component Score Bar
// ──────────────────────────────────────────────

function ComponentBar({ name, score, metricValue }) {
  const config = COMPONENT_CONFIG[name];
  if (!config) return null;
  const { label, Icon, format } = config;
  const colors = scoreColor(score);

  return (
    <div className="bg-white/[0.03] rounded-xl p-3 border border-white/5">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            {label}
          </span>
        </div>
        <span className={`text-xs font-bold ${colors.text}`}>{score}</span>
      </div>
      {/* Bar */}
      <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${colors.bg} transition-all duration-700`}
          style={{ width: `${score}%`, opacity: 0.7 }}
        />
      </div>
      {metricValue !== undefined && (
        <p className="text-[10px] text-slate-500 mt-1.5">{format(metricValue)}</p>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
// Explanation Panel
// ──────────────────────────────────────────────

function ExplanationPanel({ explanation }) {
  const [expanded, setExpanded] = useState(false);

  if (!explanation) return null;

  const { summary, strengths = [], risks = [], suggestions = [] } = explanation;

  return (
    <div className="border-t border-white/5 pt-4">
      {/* Summary always visible */}
      <p className="text-sm text-slate-300 leading-relaxed">{summary}</p>

      {/* Toggle details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 mt-3 text-[11px] font-semibold text-teal-400 hover:text-teal-300 transition-colors cursor-pointer"
      >
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        {expanded ? 'Show less' : 'View detailed breakdown'}
      </button>

      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Strengths */}
          {strengths.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">
                  Strengths
                </span>
              </div>
              <ul className="space-y-1">
                {strengths.map((s, i) => (
                  <li key={i} className="text-xs text-slate-400 pl-5 relative">
                    <span className="absolute left-1.5 top-1 w-1 h-1 rounded-full bg-emerald-400/50" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risks */}
          {risks.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">
                  Risks
                </span>
              </div>
              <ul className="space-y-1">
                {risks.map((r, i) => (
                  <li key={i} className="text-xs text-slate-400 pl-5 relative">
                    <span className="absolute left-1.5 top-1 w-1 h-1 rounded-full bg-amber-400/50" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Lightbulb className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider">
                  Suggestions
                </span>
              </div>
              <ul className="space-y-1">
                {suggestions.map((s, i) => (
                  <li key={i} className="text-xs text-slate-400 pl-5 relative">
                    <span className="absolute left-1.5 top-1 w-1 h-1 rounded-full bg-blue-400/50" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
// Window Tabs
// ──────────────────────────────────────────────

function WindowTabs({ windowDays, setWindowDays, loading }) {
  return (
    <div className="flex gap-1 bg-white/[0.03] rounded-xl p-1 border border-white/5">
      {WINDOW_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => setWindowDays(opt.value)}
          disabled={loading}
          className={`
            text-[11px] font-semibold px-3 py-1.5 rounded-lg transition-all cursor-pointer
            ${windowDays === opt.value
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

export default function HealthScoreCard({
  healthScore,
  loading,
  error,
  refresh,
  windowDays,
  setWindowDays,
}) {
  // Loading state
  if (loading && !healthScore) {
    return <SkeletonCard />;
  }

  // Error state
  if (error && !healthScore) {
    return <ErrorFallback error={error} onRetry={refresh} />;
  }

  // No data
  if (!healthScore) {
    return null;
  }

  const {
    health_score = 0,
    component_scores = {},
    metrics = {},
    explanation = {},
    has_enough_data = true,
  } = healthScore;

  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl space-y-5">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400/20 to-emerald-400/20 flex items-center justify-center">
            <Heart className="w-4 h-4 text-teal-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Financial Health Score</h4>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {healthScore.analysis_period || `Last ${windowDays} days`}
            </p>
          </div>
          {loading && healthScore && (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
          )}
        </div>

        <WindowTabs
          windowDays={windowDays}
          setWindowDays={setWindowDays}
          loading={loading}
        />
      </div>

      {/* ── Low data warning ── */}
      {!has_enough_data && (
        <div className="flex items-center gap-2 bg-amber-400/5 border border-amber-400/10 rounded-lg px-3 py-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <p className="text-[11px] text-amber-400/80">
            Limited data — score will be more accurate with more transaction history.
          </p>
        </div>
      )}

      {/* ── Score Gauge ── */}
      <ScoreGauge score={health_score} />

      {/* ── Component Scores Grid ── */}
      <div className="grid grid-cols-2 gap-3">
        <ComponentBar
          name="savings"
          score={component_scores.savings || 0}
          metricValue={metrics.savings_ratio}
        />
        <ComponentBar
          name="volatility"
          score={component_scores.volatility || 0}
          metricValue={metrics.spending_volatility}
        />
        <ComponentBar
          name="subscriptions"
          score={component_scores.subscriptions || 0}
          metricValue={metrics.recurring_burden}
        />
        <ComponentBar
          name="cash_buffer"
          score={component_scores.cash_buffer || 0}
          metricValue={metrics.cash_buffer_days}
        />
      </div>

      {/* ── Explanation Panel ── */}
      <ExplanationPanel explanation={explanation} />
    </div>
  );
}
