-- ============================================================
-- Migration 004: Add period_change column to time_range_reports
--
-- Background:
--   Migration 003 was updated to include period_change in the
--   CREATE TABLE statement. But CREATE TABLE IF NOT EXISTS does
--   NOT add new columns to an already-existing table. This
--   migration ensures the column exists regardless of whether
--   the table was created before or after the column was added
--   to 003.
--
-- Safe to run repeatedly: IF NOT EXISTS / IF EXISTS guards.
-- ============================================================

-- Add the column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'time_range_reports'
          AND column_name = 'period_change'
    ) THEN
        ALTER TABLE time_range_reports
            ADD COLUMN period_change NUMERIC(8, 2) DEFAULT 0;
    END IF;
END
$$;
