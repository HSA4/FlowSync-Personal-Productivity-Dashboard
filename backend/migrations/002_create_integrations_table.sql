-- FlowSync Database Migrations (PostgreSQL)
-- Migration: 002_create_integrations_table.sql
-- Description: Create integrations table for external service connections

-- Create sync_status enum type
DO $$ BEGIN
    CREATE TYPE sync_status_enum AS ENUM ('pending', 'in_progress', 'success', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create integrations table
CREATE TABLE IF NOT EXISTS integrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    settings JSONB,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_integrations_user_provider ON integrations(user_id, provider);
CREATE INDEX IF NOT EXISTS idx_integrations_enabled ON integrations(enabled);

-- Function to update updated_at timestamp for integrations
CREATE OR REPLACE FUNCTION update_integrations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_integrations_updated_at_trigger ON integrations;
CREATE TRIGGER update_integrations_updated_at_trigger
    BEFORE UPDATE ON integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_integrations_updated_at();

-- Create sync_logs table for tracking integration sync history
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    integration_id INTEGER NOT NULL,
    status sync_status_enum NOT NULL,
    items_synced INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT fk_integration FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE
);

-- Create indexes for sync_logs
CREATE INDEX IF NOT EXISTS idx_sync_logs_integration_status ON sync_logs(integration_id, status);
CREATE INDEX IF NOT EXISTS idx_sync_logs_started_at ON sync_logs(started_at);
