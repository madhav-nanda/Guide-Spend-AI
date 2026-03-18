-- ============================================================
-- Migration 002: Weekly Financial Intelligence Engine
-- Creates weekly_reports table for storing computed analytics.
--
-- Design decisions:
--   • account_id is NOT NULL DEFAULT 'all' (not NULL) so that
--     the UNIQUE constraint and ON CONFLICT work correctly.
--     PostgreSQL treats NULL != NULL, which would break uniqueness.
--   • JSONB columns for top_merchants / top_categories / explanation
--     keep the schema flexible for future AI enrichment.
--   • updated_at tracks idempotent regeneration timestamps.
--   • Also adds a composite index on transactions(user_id, date)
--     to accelerate the aggregation queries this engine depends on.
-- ============================================================

-- ── Table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS weekly_reports (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id      TEXT NOT NULL DEFAULT 'all',
    week_start      DATE NOT NULL,
    week_end        DATE NOT NULL,
    total_spent     NUMERIC(12, 2) DEFAULT 0,
    total_income    NUMERIC(12, 2) DEFAULT 0,
    net_change      NUMERIC(12, 2) DEFAULT 0,
    top_merchants   JSONB DEFAULT '[]'::jsonb,
    top_categories  JSONB DEFAULT '[]'::jsonb,
    week_over_week_change NUMERIC(8, 2),
    volatility_score      NUMERIC(5, 2) DEFAULT 0,
    explanation_json      JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Idempotency: one report per user + account + week
    CONSTRAINT uq_weekly_reports_user_account_week
        UNIQUE (user_id, account_id, week_start)
);

-- ── Indexes ────────────────────────────────────────────────
-- Fast lookup: latest reports for a user
CREATE INDEX IF NOT EXISTS idx_weekly_reports_user_week
    ON weekly_reports (user_id, week_start DESC);

-- ── Performance index for aggregation queries ──────────────
-- The insights engine runs SUM/GROUP BY on transactions filtered
-- by user_id + date range. This composite index covers those queries.
CREATE INDEX IF NOT EXISTS idx_transactions_user_date
    ON transactions (user_id, date);
