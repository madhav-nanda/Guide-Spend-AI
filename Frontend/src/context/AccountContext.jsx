/**
 * AccountContext — global selected-account state.
 *
 * Provides:
 *   selectedAccountId  – "all" or a plaid_account_id string
 *   setSelectedAccount – setter (persists to localStorage)
 *   resetAccount       – resets to "all" (used after disconnect / new link)
 *
 * All transaction fetching and dashboard computation reads this context.
 */
import { createContext, useContext, useState, useCallback } from 'react';

const STORAGE_KEY = 'guidespend_selected_account';

const AccountContext = createContext(null);

export function AccountProvider({ children }) {
  const [selectedAccountId, setSelectedAccountIdState] = useState(
    () => localStorage.getItem(STORAGE_KEY) || 'all'
  );

  const setSelectedAccount = useCallback((accountId) => {
    const id = accountId || 'all';
    localStorage.setItem(STORAGE_KEY, id);
    setSelectedAccountIdState(id);
  }, []);

  const resetAccount = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'all');
    setSelectedAccountIdState('all');
  }, []);

  return (
    <AccountContext.Provider
      value={{ selectedAccountId, setSelectedAccount, resetAccount }}
    >
      {children}
    </AccountContext.Provider>
  );
}

export function useAccount() {
  const context = useContext(AccountContext);
  if (!context) {
    throw new Error('useAccount must be used within an AccountProvider');
  }
  return context;
}
