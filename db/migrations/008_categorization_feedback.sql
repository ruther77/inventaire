-- Migration 008: Add categorization feedback table for ML learning
-- This table stores corrections made by users when the auto-categorization is wrong,
-- enabling future ML model training.

-- Create the feedback table
CREATE TABLE IF NOT EXISTS finance_categorization_feedback (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES finance_transactions(id) ON DELETE CASCADE,
    predicted_category_id BIGINT REFERENCES finance_categories(id) ON DELETE SET NULL,
    actual_category_id BIGINT NOT NULL REFERENCES finance_categories(id) ON DELETE CASCADE,
    confidence_score NUMERIC(4,3),  -- Original prediction confidence (0.000-1.000)
    user_id BIGINT,                  -- User who made the correction (nullable for system corrections)
    correction_source TEXT DEFAULT 'manual',  -- 'manual', 'rule', 'bulk_action'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for finding all feedback for a transaction
CREATE INDEX IF NOT EXISTS ix_categorization_feedback_transaction
    ON finance_categorization_feedback(transaction_id);

-- Index for analyzing prediction errors by category
CREATE INDEX IF NOT EXISTS ix_categorization_feedback_predicted
    ON finance_categorization_feedback(predicted_category_id);

-- Index for finding patterns in corrections by actual category
CREATE INDEX IF NOT EXISTS ix_categorization_feedback_actual
    ON finance_categorization_feedback(actual_category_id);

-- Index for time-based analysis
CREATE INDEX IF NOT EXISTS ix_categorization_feedback_created
    ON finance_categorization_feedback(created_at DESC);

COMMENT ON TABLE finance_categorization_feedback IS
    'Stores user corrections to auto-categorization for ML training';
COMMENT ON COLUMN finance_categorization_feedback.predicted_category_id IS
    'Category that was predicted/suggested by the system (NULL if no prediction)';
COMMENT ON COLUMN finance_categorization_feedback.actual_category_id IS
    'Correct category chosen by user';
COMMENT ON COLUMN finance_categorization_feedback.confidence_score IS
    'Original confidence score of the prediction (0.0-1.0)';
COMMENT ON COLUMN finance_categorization_feedback.correction_source IS
    'Source of correction: manual (user edit), rule (new rule added), bulk_action (batch correction)';
