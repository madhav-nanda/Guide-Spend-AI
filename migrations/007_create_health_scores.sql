-- ============================================================
-- Migration 007: Financial Health Score Engine
--
-- Stores computed financial health scores (0-100) with
-- component breakdowns and explainable JSON rationale.
--
-- Design decisions:
--   * SERIAL id (matches existing pattern, not UUID)
--   * account_id uses sentinel 'all' (not NULL) for correct UNIQUE
--   * analysis_window_days part of UNIQUE for separate 30/60/90 day scores
--   * component_scores stores per-metric scores (savings, volatility, etc.)
--   * explanation_json stores strengths, risks, suggestions
--   * One row per user+account+date+window — idempotent upsert
-- ============================================================

CREATE TABLE IF NOT EXISTS health_scores (
    id                     SERIAL PRIMARY KEY,
    user_id                INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id             TEXT NOT NULL DEFAULT 'all',
    as_of_date             DATE NOT NULL,
    analysis_window_days   INTEGER NOT NULL DEFAULT 90,

    health_score           INTEGER NOT NULL DEFAULT 0,

    savings_ratio          NUMERIC(8, 4) NOT NULL DEFAULT 0,
    volatility_score       NUMERIC(5, 2) NOT NULL DEFAULT 0,
    recurring_burden       NUMERIC(8, 4) NOT NULL DEFAULT 0,
    cash_buffer_days       NUMERIC(8, 2) NOT NULL DEFAULT 0,

    component_scores       JSONB NOT NULL DEFAULT '{}'::jsonb,
    explanation_json       JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_health_score_user_date_window
        UNIQUE (user_id, account_id, as_of_date, analysis_window_days)
);

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_health_score_user_date
    ON health_scores (user_id, as_of_date);

CREATE INDEX IF NOT EXISTS idx_health_score_account
    ON health_scores (user_id, account_id);
