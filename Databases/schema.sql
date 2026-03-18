-- ============================================================
-- AI-Powered Financial Management Platform
-- PostgreSQL Schema — Full Data Layer
-- ============================================================

-- 1. USERS TABLE
-- Stores registered user accounts
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(120) NOT NULL UNIQUE,
    password_hash TEXT       NOT NULL,
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- 2. TRANSACTIONS TABLE
-- Core financial records per user
CREATE TABLE transactions (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount      NUMERIC(10, 2) NOT NULL,
    category    VARCHAR(50),
    description TEXT,
    date        DATE        NOT NULL DEFAULT CURRENT_DATE,
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- 3. BUDGETS TABLE
-- Monthly spending limits per category per user
CREATE TABLE budgets (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category      VARCHAR(50) NOT NULL,
    limit_amount  NUMERIC(10, 2) NOT NULL,
    month         INTEGER     NOT NULL CHECK (month BETWEEN 1 AND 12),
    year          INTEGER     NOT NULL,
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, category, month, year)
);

-- 4. FRAUD LOGS TABLE
-- Records flagged suspicious transactions
CREATE TABLE fraud_logs (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_id    INTEGER     NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    rule_triggered    VARCHAR(100) NOT NULL,
    flagged_at        TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- 5. SAVINGS TABLE
-- Round-up savings accumulated from transactions
CREATE TABLE savings (
    id                    SERIAL PRIMARY KEY,
    user_id               INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_transaction_id INTEGER     NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    rounded_amount        NUMERIC(10, 2) NOT NULL,
    saved_at              TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- 6. RECURRING TRANSACTIONS TABLE
-- Detected subscription/recurring patterns
CREATE TABLE recurring_transactions (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant         VARCHAR(100) NOT NULL,
    average_amount   NUMERIC(10, 2) NOT NULL,
    frequency_days   INTEGER     NOT NULL,
    last_seen        DATE        NOT NULL,
    annual_estimate  NUMERIC(10, 2),
    created_at       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, merchant)
);

-- ============================================================
-- INDEXES — improve query performance
-- ============================================================
CREATE INDEX idx_transactions_user_id  ON transactions(user_id);
CREATE INDEX idx_transactions_date     ON transactions(date);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_fraud_logs_user_id    ON fraud_logs(user_id);
CREATE INDEX idx_savings_user_id       ON savings(user_id);
CREATE INDEX idx_recurring_user_id     ON recurring_transactions(user_id);
