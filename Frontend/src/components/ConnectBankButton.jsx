import { useState, useCallback } from 'react';
import { usePlaidLink } from 'react-plaid-link';
import { Link as LinkIcon, Loader2 } from 'lucide-react';
import { plaidApi } from '../api/plaidApi';

export default function ConnectBankButton({ onSuccess }) {
  const [linkToken, setLinkToken] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Step 1: Get a link token from our backend
  const generateLinkToken = async () => {
    setLoading(true);
    try {
      const data = await plaidApi.createLinkToken();
      setLinkToken(data.link_token);
    } catch (err) {
      console.error('Failed to create link token:', err.message);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: After Plaid Link succeeds, exchange the token and sync
  const onPlaidSuccess = useCallback(
    async (publicToken, metadata) => {
      setSyncing(true);
      try {
        await plaidApi.exchangeToken(
          publicToken,
          metadata.institution?.institution_id || '',
          metadata.institution?.name || ''
        );

        await plaidApi.syncTransactions();

        if (onSuccess) onSuccess();
      } catch (err) {
        console.error('Failed to link bank:', err.message);
      } finally {
        setSyncing(false);
        setLinkToken(null);
      }
    },
    [onSuccess]
  );

  // Step 2: Open Plaid Link widget
  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: onPlaidSuccess,
    onExit: () => setLinkToken(null),
  });

  // Auto-open Plaid Link when linkToken arrives
  if (linkToken && ready) {
    open();
  }

  return (
    <>
      {syncing ? (
        <button
          disabled
          className="inline-flex items-center gap-2 backdrop-blur-xl bg-teal-500/10 border border-teal-500/20 text-teal-400 px-5 py-2.5 rounded-xl text-sm font-semibold"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          Syncing Transactions...
        </button>
      ) : (
        <button
          onClick={generateLinkToken}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-400 hover:to-blue-500 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer disabled:cursor-not-allowed shadow-lg shadow-teal-500/20"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Connecting...
            </>
          ) : (
            <>
              <LinkIcon className="w-4 h-4" />
              Connect Bank Account
            </>
          )}
        </button>
      )}
    </>
  );
}
