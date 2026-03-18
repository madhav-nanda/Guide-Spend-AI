-- ============================================================
-- Migration 005: Subscription Detection — recurring_merchants
--
-- Stores detected recurring transactions (subscriptions/bills).
-- Deterministic heuristics, not ML — explainable and auditable.
--
-- Design decisions:
--   * merchant_key is a normalized stable identifier for grouping
--   * account_id uses sentinel 'all' (not NULL) for correct UNIQUE
--   * last_n_transactions stores compact JSONB array for UI display
--   * explanation_json stores full detection evidence
--   * UNIQUE on (user_id, account_id, merchant_key, cadence) for upsert
-- ============================================================

CREATE TABLE IF NOT EXISTS recurring_merchants (
    id                    SERIAL PRIMARY KEY,
    user_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id            TEXT NOT NULL DEFAULT 'all',
    merchant_key          TEXT NOT NULL,
    merchant_display_name TEXT NOT NULL,
    cadence               TEXT NOT NULL DEFAULT 'unknown',
    avg_amount            NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_stddev         NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_tolerance      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    last_charge_date      DATE,
    next_expected_date    DATE,
    confidence_score      NUMERIC(5, 2) NOT NULL DEFAULT 0,
    sample_size           INTEGER NOT NULL DEFAULT 0,
    last_n_transactions   JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation_json      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_recurring_merchants_user_merchant
        UNIQUE (user_id, account_id, merchant_key, cadence)
);

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_recurring_user_next
    ON recurring_merchants (user_id, next_expected_date);

CREATE INDEX IF NOT EXISTS idx_recurring_confidence
    ON recurring_merchants (user_id, confidence_score DESC);


-- ============================================================
-- recurring_events — audit trail linking detected subscriptions
-- to individual transactions
-- ============================================================

CREATE TABLE IF NOT EXISTS recurring_events (
    id              SERIAL PRIMARY KEY,
    recurring_id    INTEGER NOT NULL REFERENCES recurring_merchants(id) ON DELETE CASCADE,
    transaction_id  INTEGER,
    date            DATE NOT NULL,
    amount          NUMERIC(12, 2) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recurring_events_recurring
    ON recurring_events (recurring_id);
