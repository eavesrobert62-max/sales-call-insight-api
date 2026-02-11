-- Initialize database with some sample data
-- This file runs when PostgreSQL container starts for the first time

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_calls_rep_id ON calls(rep_id);
CREATE INDEX IF NOT EXISTS idx_calls_team_id ON calls(team_id);
CREATE INDEX IF NOT EXISTS idx_calls_processing_status ON calls(processing_status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);

CREATE INDEX IF NOT EXISTS idx_analysis_results_call_id ON analysis_results(call_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_deal_score ON analysis_results(deal_score);

CREATE INDEX IF NOT EXISTS idx_usage_logs_rep_id ON usage_logs(rep_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_reps_team_id ON reps(team_id);
CREATE INDEX IF NOT EXISTS idx_reps_email ON reps(email);

-- Insert sample team
INSERT INTO teams (name, tier) VALUES 
('Enterprise Sales', 'business'),
('SMB Sales', 'professional')
ON CONFLICT DO NOTHING;

-- Insert sample reps (passwords are hashed versions of "password123")
INSERT INTO reps (name, email, team_id, tier, api_key_hash, is_active) VALUES 
('John Smith', 'john@company.com', 1, 'business', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm', true),
('Sarah Johnson', 'sarah@company.com', 1, 'business', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm', true),
('Mike Wilson', 'mike@company.com', 2, 'professional', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm', true)
ON CONFLICT (email) DO NOTHING;

-- Update team managers
UPDATE teams SET manager_id = 1 WHERE id = 1;
UPDATE teams SET manager_id = 3 WHERE id = 2;
