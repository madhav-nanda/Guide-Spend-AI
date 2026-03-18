-- ============================================================
-- Migration 006: Cash Flow Forecast + Overdraft Risk
--
-- Stores deterministic daily-balance projections for 7/14 days.
-- Uses current balances, recent spending, and detected subscriptions.
--
-- Design decisions:
--   * horizon_days is part of UNIQUE key (separate 7-day and 14-day)
--   * projected_daily_balances is JSONB array [{date, balance}, ...]
--   * drivers_json stores the inputs used for the forecast
--   * explanation_json stores human-readable risk rationale
--   * One row per user+account+date+horizon — idempotent upsert
-- ============================================================

CREATE TABLE IF NOT EXISTS cashflow_forecasts (
    id                       SERIAL PRIMARY KEY,
    user_id                  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id               TEXT NOT NULL DEFAULT 'all',
    as_of_date               DATE NOT NULL,
    horizon_days             INTEGER NOT NULL,
    starting_balance         NUMERIC(12, 2) NOT NULL DEFAULT 0,
    projected_end_balance    NUMERIC(12, 2) NOT NULL DEFAULT 0,
    min_projected_balance    NUMERIC(12, 2) NOT NULL DEFAULT 0,
    risk_score               NUMERIC(5, 2) NOT NULL DEFAULT 0,
    projected_daily_balances JSONB NOT NULL DEFAULT '[]'::jsonb,
    drivers_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
    explanation_json         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_cashflow_user_date_horizon
        UNIQUE (user_id, account_id, as_of_date, horizon_days)
);

-- Fast lookups
CREATE INDEX IF NOT EXISTS idx_cashflow_user_date
    ON cashflow_forecasts (user_id, as_of_date);

CREATE INDEX IF NOT EXISTS idx_cashflow_risk
    ON cashflow_forecasts (risk_score DESC);
