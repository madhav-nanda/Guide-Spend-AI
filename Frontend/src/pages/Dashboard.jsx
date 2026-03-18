import { useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useAccount } from '../context/AccountContext';
import { useAccounts } from '../hooks/useAccounts';
import { useTransactions } from '../hooks/useTransactions';
import { useTimeRangeInsights } from '../hooks/useTimeRangeInsights';
import { useSubscriptions } from '../hooks/useSubscriptions';
import { useCashflowForecast } from '../hooks/useCashflowForecast';
import { useHealthScore } from '../hooks/useHealthScore';
import BackgroundLayer from '../components/BackgroundLayer';
import BalanceCard from '../components/BalanceCard';
import ConnectBankButton from '../components/ConnectBankButton';
import TransactionsTable from '../components/TransactionsTable';
import Charts from '../components/Charts';
import InsightsCard from '../components/InsightsCard';
import SubscriptionsCard from '../components/SubscriptionsCard';
import CashflowCard from '../components/CashflowCard';
import HealthScoreCard from '../components/HealthScoreCard';
import { Sparkles, LogOut, Filter, AlertCircle } from 'lucide-react';

export default function Dashboard() {
  const { logout } = useAuth();
  const { selectedAccountId, setSelectedAccount, resetAccount } = useAccount();
  const { validAccounts, loading: accountsLoading, error: accountsError, fetchAccounts } = useAccounts();
  const {
    transactions,
    pagination,
    loading: txnsLoading,
    error: txnsError,
    fetchTransactions,
    nextPage,
    prevPage,
  } = useTransactions();
  const {
    data: insightsData,
    loading: insightsLoading,
    error: insightsError,
    refresh: refreshInsights,
    mode: insightsMode,
    setMode: setInsightsMode,
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
  } = useTimeRangeInsights();
  const {
    subscriptions,
    count: subscriptionCount,
    loading: subsLoading,
    error: subsError,
    refresh: refreshSubscriptions,
    recompute: recomputeSubscriptions,
    recomputing: subsRecomputing,
  } = useSubscriptions();

  // ── Cashflow: pass totalBalance as starting balance ──
  // (will be set after accounts load; useCashflowForecast re-fetches when it changes)
  const {
    forecast: cashflowForecast,
    loading: cashflowLoading,
    error: cashflowError,
    refresh: refreshCashflow,
    horizonDays,
    setHorizonDays,
  } = useCashflowForecast(null); // balance passed after render via totalBalance

  // ── Health Score: pass totalBalance as current balance ──
  const {
    healthScore: healthScoreData,
    loading: healthLoading,
    error: healthError,
    refresh: refreshHealthScore,
    windowDays: healthWindowDays,
    setWindowDays: setHealthWindowDays,
  } = useHealthScore(null); // balance passed after render via totalBalance

  // ── Initial fetch on mount + when account filter changes ──
  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  useEffect(() => {
    fetchTransactions({
      page: 1,
      account_id: selectedAccountId,
    });
  }, [selectedAccountId, fetchTransactions]);

  // ── After connecting a new bank ──
  const handleBankConnected = useCallback(() => {
    resetAccount();
    fetchAccounts();
    fetchTransactions({ page: 1, account_id: 'all' });
    refreshInsights();
    refreshSubscriptions();
    refreshCashflow();
    refreshHealthScore();
  }, [resetAccount, fetchAccounts, fetchTransactions, refreshInsights, refreshSubscriptions, refreshCashflow, refreshHealthScore]);

  // ── After disconnecting a bank ──
  const handleDisconnect = useCallback(() => {
    resetAccount();
    fetchAccounts();
    fetchTransactions({ page: 1, account_id: 'all' });
    refreshInsights();
    refreshSubscriptions();
    refreshCashflow();
    refreshHealthScore();
  }, [resetAccount, fetchAccounts, fetchTransactions, refreshInsights, refreshSubscriptions, refreshCashflow, refreshHealthScore]);

  // ── Handle page navigation (preserves selected account) ──
  const handleNextPage = useCallback(() => {
    nextPage(selectedAccountId);
  }, [nextPage, selectedAccountId]);

  const handlePrevPage = useCallback(() => {
    prevPage(selectedAccountId);
  }, [prevPage, selectedAccountId]);

  // ── Derived data ──
  const accountOptions = validAccounts.map((a) => ({
    account_id: a.account_id,
    label: `${a.institution_name || 'Bank'} – ${a.name}`,
  }));

  const totalBalance =
    selectedAccountId === 'all'
      ? validAccounts.reduce((sum, a) => sum + (a.current_balance || 0), 0)
      : validAccounts
          .filter((a) => a.account_id === selectedAccountId)
          .reduce((sum, a) => sum + (a.current_balance || 0), 0);

  const totalSpending = transactions
    .filter((t) => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  const totalIncome = transactions
    .filter((t) => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);

  const accountCountLabel =
    selectedAccountId === 'all'
      ? `Across ${validAccounts.length} account${validAccounts.length !== 1 ? 's' : ''}`
      : accountOptions.find((a) => a.account_id === selectedAccountId)?.label || '1 account';

  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  }

  const summaryCards = [
    {
      label: 'Total Balance',
      value: formatCurrency(totalBalance),
      sub: accountCountLabel,
      color: 'text-white',
    },
    {
      label: 'Total Income',
      value: formatCurrency(totalIncome),
      sub: 'From filtered transactions',
      color: 'text-emerald-400',
    },
    {
      label: 'Total Spending',
      value: formatCurrency(totalSpending),
      sub: `${transactions.filter((t) => t.amount < 0).length} expense transactions`,
      color: 'text-rose-400',
    },
  ];

  const isLoading = accountsLoading || txnsLoading;
  const globalError = accountsError || txnsError;

  return (
    <BackgroundLayer>
      {/* Sandbox Demo Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2.5 text-center">
        <p className="text-amber-300 text-xs sm:text-sm font-medium">
          ⚠️ This is a sandbox/demo environment. No real bank accounts are connected. All data is simulated.
        </p>
      </div>

      {/* Sticky Navbar */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/70 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500/20 to-blue-600/20 border border-white/10 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-teal-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight tracking-tight">
                GuideSpend AI
              </h1>
              <p className="text-[10px] text-slate-500 leading-tight">Smart Spending. Clear Decisions.</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white border border-white/10 hover:border-white/20 px-3.5 py-1.5 rounded-lg transition-all cursor-pointer backdrop-blur-sm"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8 pb-16">
        {/* Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Dashboard</h2>
            <p className="text-slate-400 text-sm mt-0.5">Your financial overview at a glance</p>
          </div>
          <ConnectBankButton onSuccess={handleBankConnected} />
        </div>

        {/* ── Global Error Banner ── */}
        {globalError && (
          <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/20 rounded-xl px-5 py-3.5">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <p className="text-sm text-rose-300">{globalError}</p>
          </div>
        )}

        {isLoading && !transactions.length && !validAccounts.length ? (
          <div className="flex items-center justify-center py-24">
            <div className="flex items-center gap-3 text-slate-400">
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading dashboard...
            </div>
          </div>
        ) : (
          <>
            {/* ── Account Filter Dropdown ── */}
            {validAccounts.length > 0 && (
              <div className="flex items-center gap-3">
                <Filter className="w-4 h-4 text-slate-400" />
                <label className="text-sm text-slate-400 font-medium">Filter by Account:</label>
                <select
                  value={selectedAccountId}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="backdrop-blur-xl bg-white/5 border border-white/10 text-white text-sm rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500/40 transition-all appearance-none cursor-pointer min-w-[240px]"
                  style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 12px center',
                    paddingRight: '36px',
                  }}
                >
                  <option value="all" className="bg-slate-800 text-white">
                    All Accounts
                  </option>
                  {accountOptions.map((opt) => (
                    <option
                      key={opt.account_id}
                      value={opt.account_id}
                      className="bg-slate-800 text-white"
                    >
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {summaryCards.map((card) => (
                <div
                  key={card.label}
                  className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 shadow-xl hover:shadow-2xl hover:-translate-y-0.5 transition-all duration-300"
                >
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    {card.label}
                  </p>
                  <p className={`text-3xl font-extrabold mt-2 ${card.color}`}>
                    {card.value}
                  </p>
                  <p className="text-xs text-slate-500 mt-2">{card.sub}</p>
                </div>
              ))}
            </div>

            {/* Financial Health Score */}
            <section>
              <HealthScoreCard
                healthScore={healthScoreData}
                loading={healthLoading}
                error={healthError}
                refresh={refreshHealthScore}
                windowDays={healthWindowDays}
                setWindowDays={setHealthWindowDays}
                currentBalance={totalBalance}
              />
            </section>

            {/* Financial Insights */}
            <section>
              <InsightsCard
                data={insightsData}
                loading={insightsLoading}
                error={insightsError}
                refresh={refreshInsights}
                mode={insightsMode}
                setMode={setInsightsMode}
                prevPeriod={prevPeriod}
                nextPeriod={nextPeriod}
                canGoNext={canGoNext}
                goToToday={goToToday}
                rollingDays={rollingDays}
                setRollingDays={setRollingDays}
                customStart={customStart}
                customEnd={customEnd}
                setCustomRange={setCustomRange}
                applyCustomRange={applyCustomRange}
              />
            </section>

            {/* Subscriptions & Cash Flow — side by side on large screens */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <section>
                <SubscriptionsCard
                  subscriptions={subscriptions}
                  count={subscriptionCount}
                  loading={subsLoading}
                  error={subsError}
                  refresh={refreshSubscriptions}
                  recompute={recomputeSubscriptions}
                  recomputing={subsRecomputing}
                />
              </section>
              <section>
                <CashflowCard
                  forecast={cashflowForecast}
                  loading={cashflowLoading}
                  error={cashflowError}
                  refresh={refreshCashflow}
                  horizonDays={horizonDays}
                  setHorizonDays={setHorizonDays}
                />
              </section>
            </div>

            {/* Linked Accounts */}
            {validAccounts.length > 0 && (
              <section>
                <h3 className="text-lg font-semibold text-white mb-4">Linked Accounts</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {validAccounts.map((account) => (
                    <BalanceCard
                      key={account.account_id}
                      account={account}
                      onDisconnect={handleDisconnect}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Charts */}
            {transactions.length > 0 && (
              <section>
                <h3 className="text-lg font-semibold text-white mb-4">
                  Analytics
                  {selectedAccountId !== 'all' && (
                    <span className="text-sm font-normal text-slate-400 ml-2">
                      (filtered)
                    </span>
                  )}
                </h3>
                <Charts transactions={transactions} />
              </section>
            )}

            {/* Transactions */}
            <section>
              <h3 className="text-lg font-semibold text-white mb-4">
                Recent Transactions
                {selectedAccountId !== 'all' && (
                  <span className="text-sm font-normal text-slate-400 ml-2">
                    (filtered)
                  </span>
                )}
              </h3>
              <TransactionsTable
                transactions={transactions}
                pagination={pagination}
                loading={txnsLoading}
                onNextPage={handleNextPage}
                onPrevPage={handlePrevPage}
              />
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 mt-8">
        <p className="text-center text-xs text-slate-600">
          GuideSpend AI &mdash; Smart Spending. Clear Decisions.
        </p>
      </footer>
    </BackgroundLayer>
  );
}
