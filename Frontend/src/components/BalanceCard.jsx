import { useState } from 'react';
import { Landmark, CreditCard, Building2, TrendingUp, Unplug, Loader2, X, AlertTriangle } from 'lucide-react';
import { plaidApi } from '../api/plaidApi';

const typeConfig = {
  depository: { icon: Landmark, color: 'text-teal-400', bg: 'bg-teal-400/10' },
  credit: { icon: CreditCard, color: 'text-orange-400', bg: 'bg-orange-400/10' },
  loan: { icon: Building2, color: 'text-rose-400', bg: 'bg-rose-400/10' },
  investment: { icon: TrendingUp, color: 'text-blue-400', bg: 'bg-blue-400/10' },
};

function formatCurrency(amount) {
  if (amount == null) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

export default function BalanceCard({ account, onDisconnect }) {
  const config = typeConfig[account.type] || typeConfig.depository;
  const Icon = config.icon;

  const [showConfirm, setShowConfirm] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState(null);

  const handleDisconnect = async () => {
    if (disconnecting) return; // Prevent double-click
    setDisconnecting(true);
    setError(null);
    try {
      await plaidApi.disconnect(account.item_id);
      setShowConfirm(false);
      if (onDisconnect) onDisconnect();
    } catch (err) {
      setError(err.message || 'Failed to disconnect account');
    } finally {
      setDisconnecting(false);
    }
  };

  return (
    <>
      <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-5 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 group relative">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${config.bg}`}>
              <Icon className={`w-5 h-5 ${config.color}`} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white leading-tight">{account.name}</h3>
              <p className="text-xs text-slate-500 capitalize">{account.subtype || account.type}</p>
            </div>
          </div>
          {account.mask && (
            <span className="text-xs text-slate-500 font-mono bg-white/5 px-2 py-0.5 rounded-md border border-white/5">
              ****{account.mask}
            </span>
          )}
        </div>

        {/* Balances */}
        <div className="space-y-1.5">
          <div className="flex items-baseline justify-between">
            <span className="text-xs text-slate-500">Current</span>
            <span className="text-lg font-bold text-white">
              {formatCurrency(account.current_balance)}
            </span>
          </div>
          {account.available_balance != null && (
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-slate-500">Available</span>
              <span className="text-sm font-medium text-slate-300">
                {formatCurrency(account.available_balance)}
              </span>
            </div>
          )}
        </div>

        {/* Institution + Disconnect */}
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
          <p className="text-xs text-slate-500 truncate">{account.institution_name}</p>
          <button
            onClick={() => setShowConfirm(true)}
            className="opacity-0 group-hover:opacity-100 inline-flex items-center gap-1 text-[11px] text-rose-400/70 hover:text-rose-400 transition-all cursor-pointer px-2 py-1 rounded-lg hover:bg-rose-400/10"
            title="Disconnect account"
          >
            <Unplug className="w-3 h-3" />
            Disconnect
          </button>
        </div>
      </div>

      {/* ── Confirmation Modal ── */}
      {showConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => !disconnecting && setShowConfirm(false)}
          />

          {/* Modal */}
          <div className="relative bg-slate-900 border border-white/10 rounded-2xl shadow-2xl max-w-md w-full p-6">
            {/* Close button */}
            <button
              onClick={() => !disconnecting && setShowConfirm(false)}
              className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors cursor-pointer"
              disabled={disconnecting}
            >
              <X className="w-5 h-5" />
            </button>

            {/* Icon */}
            <div className="w-12 h-12 rounded-xl bg-rose-400/10 flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6 text-rose-400" />
            </div>

            {/* Text */}
            <h3 className="text-lg font-semibold text-white">Disconnect Account?</h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              This will disconnect{' '}
              <span className="text-white font-medium">
                {account.institution_name} – {account.name}
              </span>{' '}
              and permanently remove all associated transactions from your dashboard.
            </p>
            <p className="text-xs text-slate-500 mt-2">This action cannot be undone.</p>

            {/* Error display */}
            {error && (
              <div className="mt-3 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                <p className="text-xs text-rose-300">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={() => setShowConfirm(false)}
                disabled={disconnecting}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-300 border border-white/10 rounded-xl hover:bg-white/5 transition-all cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-rose-500 hover:bg-rose-600 rounded-xl transition-all cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {disconnecting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Disconnecting...
                  </>
                ) : (
                  <>
                    <Unplug className="w-4 h-4" />
                    Disconnect
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
