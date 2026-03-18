import { ClipboardList, Building2, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    signDisplay: 'always',
  }).format(amount);
}

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

const categoryColors = {
  FOOD_AND_DRINK: 'bg-amber-400/10 text-amber-400 border-amber-400/20',
  TRANSPORTATION: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  TRANSFER_OUT: 'bg-rose-400/10 text-rose-400 border-rose-400/20',
  TRANSFER_IN: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  ENTERTAINMENT: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  TRAVEL: 'bg-sky-400/10 text-sky-400 border-sky-400/20',
  GENERAL_MERCHANDISE: 'bg-slate-400/10 text-slate-300 border-slate-400/20',
  RENT_AND_UTILITIES: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
  INCOME: 'bg-green-400/10 text-green-400 border-green-400/20',
  LOAN_PAYMENTS: 'bg-rose-400/10 text-rose-300 border-rose-400/20',
};

function getCategoryColor(category) {
  return categoryColors[category] || 'bg-slate-400/10 text-slate-400 border-slate-400/20';
}

function formatCategory(category) {
  if (!category) return 'Other';
  return category
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatAccountLabel(txn) {
  if (txn.source !== 'plaid') return null;
  const inst = txn.institution_name || '';
  const acct = txn.account_name || '';
  if (inst && acct) return `${inst} – ${acct}`;
  if (inst) return inst;
  if (acct) return acct;
  return 'Bank Account';
}

export default function TransactionsTable({
  transactions,
  pagination,
  loading,
  onNextPage,
  onPrevPage,
}) {
  const { page = 1, total_pages = 1, total = 0 } = pagination || {};

  if (!transactions || transactions.length === 0) {
    return (
      <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-12 text-center">
        {loading ? (
          <div className="flex items-center justify-center gap-2 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Loading transactions...</span>
          </div>
        ) : (
          <>
            <ClipboardList className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No transactions yet.</p>
            <p className="text-slate-500 text-sm mt-1">Connect a bank account to import transactions.</p>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 overflow-hidden shadow-xl">
      {/* Loading overlay for page transitions */}
      {loading && (
        <div className="px-5 py-2 bg-teal-500/5 border-b border-teal-500/10 flex items-center gap-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-400" />
          <span className="text-xs text-teal-400">Loading...</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-5 py-3.5 sticky top-0 backdrop-blur-xl bg-white/5">
                Date
              </th>
              <th className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-5 py-3.5 sticky top-0 backdrop-blur-xl bg-white/5">
                Description
              </th>
              <th className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-5 py-3.5 sticky top-0 backdrop-blur-xl bg-white/5">
                Account
              </th>
              <th className="text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-5 py-3.5 sticky top-0 backdrop-blur-xl bg-white/5">
                Category
              </th>
              <th className="text-right text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-5 py-3.5 sticky top-0 backdrop-blur-xl bg-white/5">
                Amount
              </th>
              <th className="text-center text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-5 py-3.5 sticky top-0 backdrop-blur-xl bg-white/5">
                Source
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {transactions.map((txn) => {
              const accountLabel = formatAccountLabel(txn);

              return (
                <tr key={txn.id} className="hover:bg-white/[0.03] transition-colors">
                  <td className="px-5 py-3.5 text-sm text-slate-300 whitespace-nowrap">
                    {formatDate(txn.date)}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-white font-medium max-w-[220px] truncate">
                    {txn.description}
                  </td>
                  <td className="px-5 py-3.5 text-sm whitespace-nowrap">
                    {accountLabel ? (
                      <span className="inline-flex items-center gap-1.5 text-slate-300">
                        <Building2 className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="truncate max-w-[160px]">{accountLabel}</span>
                      </span>
                    ) : (
                      <span className="text-slate-500 text-xs">Manual</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`inline-block text-[11px] font-medium px-2.5 py-1 rounded-full border ${getCategoryColor(txn.category)}`}
                    >
                      {formatCategory(txn.category)}
                    </span>
                  </td>
                  <td
                    className={`px-5 py-3.5 text-sm font-semibold text-right whitespace-nowrap ${
                      txn.amount >= 0 ? 'text-emerald-400' : 'text-slate-200'
                    }`}
                  >
                    {formatCurrency(txn.amount)}
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    <span
                      className={`inline-block text-[11px] font-medium px-2.5 py-0.5 rounded-md border ${
                        txn.source === 'plaid'
                          ? 'bg-indigo-400/10 text-indigo-400 border-indigo-400/20'
                          : 'bg-white/5 text-slate-400 border-white/10'
                      }`}
                    >
                      {txn.source === 'plaid' ? 'Bank' : 'Manual'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── Footer with Pagination Controls ── */}
      <div className="border-t border-white/5 px-5 py-3 bg-white/[0.02] flex items-center justify-between">
        <p className="text-xs text-slate-500">
          {total > 0
            ? `Showing ${(page - 1) * (pagination?.per_page || 50) + 1}–${Math.min(
                page * (pagination?.per_page || 50),
                total
              )} of ${total}`
            : `${transactions.length} transaction${transactions.length !== 1 ? 's' : ''}`}
        </p>

        {total_pages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={onPrevPage}
              disabled={page <= 1 || loading}
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white border border-white/10 hover:border-white/20 px-2.5 py-1.5 rounded-lg transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              Prev
            </button>
            <span className="text-xs text-slate-400 px-2">
              Page <span className="text-white font-medium">{page}</span> of{' '}
              <span className="text-white font-medium">{total_pages}</span>
            </span>
            <button
              onClick={onNextPage}
              disabled={page >= total_pages || loading}
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white border border-white/10 hover:border-white/20 px-2.5 py-1.5 rounded-lg transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
