-- ============================================================
-- Migration 003: Generalized Time-Range Reports
--
-- Replaces the week-only weekly_reports table with a flexible
-- time_range_reports table that supports week, month, rolling,
-- and custom date ranges.
--
-- Design decisions:
--   • granularity column stores the report type (week/month/rolling/custom)
--     enabling per-type cache lookup and analytics.
--   • UNIQUE on (user_id, account_id, start_date, end_date) means
--     one cached report per user + account + exact date window.
--   • account_id NOT NULL DEFAULT 'all' — same pattern as weekly_reports
--     so UNIQUE / ON CONFLICT work correctly (NULL != NULL in PG).
--   • Keeps the old weekly_reports table untouched for safety.
--     The new endpoint reads from time_range_reports exclusively.
-- ============================================================

-- ── Table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS time_range_reports (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id      TEXT NOT NULL DEFAULT 'all',
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    granularity     TEXT NOT NULL DEFAULT 'week',
    total_spent     NUMERIC(12, 2) DEFAULT 0,
    total_income    NUMERIC(12, 2) DEFAULT 0,
    net_change      NUMERIC(12, 2) DEFAULT 0,
    top_merchants   JSONB DEFAULT '[]'::jsonb,
    top_categories  JSONB DEFAULT '[]'::jsonb,
    volatility_score NUMERIC(5, 2) DEFAULT 0,
    period_change   NUMERIC(8, 2) DEFAULT 0,
    explanation_json JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Idempotency: one report per user + account + exact date range
    CONSTRAINT uq_time_range_reports_user_dates
        UNIQUE (user_id, account_id, start_date, end_date)
);

-- ── Indexes ────────────────────────────────────────────────
-- Fast cache lookup by user + date range
CREATE INDEX IF NOT EXISTS idx_time_range_user_dates
    ON time_range_reports (user_id, start_date, end_date);

-- Filter by granularity for analytics / cleanup
CREATE INDEX IF NOT EXISTS idx_time_range_granularity
    ON time_range_reports (granularity);
