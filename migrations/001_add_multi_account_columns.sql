-- Migration: Add multi-account support to transactions table
-- Date: 2026-03-02
-- Purpose: Track which specific bank account each transaction belongs to

-- Add plaid_account_id to link transactions to specific bank accounts
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS plaid_account_id VARCHAR;

-- Add institution_name for display (e.g., Chase, Bank of America)
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS institution_name VARCHAR;

-- Add account_name for display (e.g., Plaid Checking, Plaid Savings)
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS account_name VARCHAR;

-- Index for fast filtering by account
CREATE INDEX IF NOT EXISTS idx_transactions_plaid_account_id
ON transactions (plaid_account_id);

-- Composite index for user + account filtering
CREATE INDEX IF NOT EXISTS idx_transactions_user_account
ON transactions (user_id, plaid_account_id);
