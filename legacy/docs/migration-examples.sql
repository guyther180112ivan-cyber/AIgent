-- Migration Examples for AIgent Platform
-- Common migration patterns and examples

-- Migration 001: Initial schema
-- This is the base schema (see postgresql-schema.sql)

-- Migration 002: Add user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'auto')),
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id) WHERE deleted_at IS NULL;

-- Add trigger for updated_at
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration 003: Add skill categories
ALTER TABLE skills ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE skills ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';

CREATE INDEX idx_skills_category ON skills(category) WHERE deleted_at IS NULL;
CREATE INDEX idx_skills_tags ON skills USING GIN(tags) WHERE deleted_at IS NULL;

-- Update existing skills with categories
UPDATE skills SET category = 'general' WHERE name = 'General Assistant';
UPDATE skills SET category = 'development' WHERE name = 'Code Helper';
UPDATE skills SET category = 'creative' WHERE name = 'Creative Writer';
UPDATE skills SET category = 'analytics' WHERE name = 'Data Analyst';

-- Migration 004: Add conversation metadata
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_conversations_message_count ON conversations(message_count DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_pinned ON conversations(is_pinned, last_message_at DESC) WHERE deleted_at IS NULL;

-- Migration 005: Add tool usage statistics
CREATE TABLE IF NOT EXISTS tool_usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    total_execution_time_ms BIGINT DEFAULT 0,
    average_execution_time_ms DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, tool_id)
);

CREATE INDEX idx_tool_usage_stats_user_id ON tool_usage_stats(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tool_usage_stats_tool_id ON tool_usage_stats(tool_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tool_usage_stats_usage_count ON tool_usage_stats(usage_count DESC) WHERE deleted_at IS NULL;

-- Add trigger for updated_at
CREATE TRIGGER update_tool_usage_stats_updated_at BEFORE UPDATE ON tool_usage_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration 006: Add message reactions
ALTER TABLE messages ADD COLUMN IF NOT EXISTS reactions JSONB DEFAULT '{}';

-- Example reaction format:
-- {
--   "👍": 3,
--   "❤️": 1,
--   "🤔": 2
-- }

CREATE INDEX idx_messages_reactions ON messages USING GIN(reactions) WHERE deleted_at IS NULL;

-- Migration 007: Add skill proficiency levels
ALTER TABLE user_skills ADD COLUMN IF NOT EXISTS proficiency_level INTEGER DEFAULT 1 
CHECK (proficiency_level BETWEEN 1 AND 5);
ALTER TABLE user_skills ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE user_skills ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX idx_user_skills_proficiency ON user_skills(proficiency_level DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_skills_usage_count ON user_skills(usage_count DESC) WHERE deleted_at IS NULL;

-- Migration 008: Add conversation sharing
CREATE TABLE IF NOT EXISTS conversation_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversation_shares_token ON conversation_shares(share_token) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversation_shares_conversation_id ON conversation_shares(conversation_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversation_shares_public ON conversation_shares(is_public, created_at DESC) WHERE deleted_at IS NULL;

-- Migration 009: Add API keys for external integrations
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    permissions JSONB NOT NULL DEFAULT '[]',
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash) WHERE deleted_at IS NULL;
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE deleted_at IS NULL;

-- Add trigger for updated_at
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration 010: Add audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- Example trigger for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (action, table_name, record_id, new_values)
        VALUES ('INSERT', TG_TABLE_NAME, NEW.id, row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (action, table_name, record_id, old_values, new_values)
        VALUES ('UPDATE', TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (action, table_name, record_id, old_values)
        VALUES ('DELETE', TG_TABLE_NAME, OLD.id, row_to_json(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to important tables
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_agents_trigger
    AFTER INSERT OR UPDATE OR DELETE ON agents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Migration 011: Add conversation templates
CREATE TABLE IF NOT EXISTS conversation_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    initial_message TEXT NOT NULL,
    required_skills JSONB DEFAULT '[]',
    required_tools JSONB DEFAULT '[]',
    category VARCHAR(100),
    is_public BOOLEAN DEFAULT FALSE,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversation_templates_category ON conversation_templates(category) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversation_templates_public ON conversation_templates(is_public, usage_count DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversation_templates_created_by ON conversation_templates(created_by_user_id) WHERE deleted_at IS NULL;

-- Add trigger for updated_at
CREATE TRIGGER update_conversation_templates_updated_at BEFORE UPDATE ON conversation_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Migration 012: Add rate limiting
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INTEGER DEFAULT 0,
    limit_type VARCHAR(50) NOT NULL, -- 'messages', 'tool_calls', 'api_calls'
    limit_value INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rate_limits_user_window ON rate_limits(user_id, window_start, window_end);
CREATE INDEX idx_rate_limits_type ON rate_limits(limit_type);

-- Migration 013: Add backup and restore functionality
CREATE TABLE IF NOT EXISTS backups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    backup_type VARCHAR(50) NOT NULL, -- 'full', 'conversations', 'settings'
    file_path VARCHAR(500),
    file_size BIGINT,
    checksum VARCHAR(64),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_backups_user_id ON backups(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_backups_type ON backups(backup_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_backups_status ON backups(status) WHERE deleted_at IS NULL;

-- Example stored procedures for common operations

-- Procedure to get user's active skills with their configurations
CREATE OR REPLACE FUNCTION get_user_active_skills(p_user_id UUID)
RETURNS TABLE (
    skill_id UUID,
    skill_name VARCHAR(255),
    skill_description TEXT,
    skill_config JSONB,
    proficiency_level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.name,
        s.description,
        us.config,
        us.proficiency_level
    FROM user_skills us
    JOIN skills s ON us.skill_id = s.id
    WHERE us.user_id = p_user_id
      AND us.deleted_at IS NULL
      AND s.deleted_at IS NULL
      AND us.is_enabled = TRUE
      AND s.is_active = TRUE
    ORDER BY us.proficiency_level DESC, s.name;
END;
$$ LANGUAGE plpgsql;

-- Procedure to update conversation message count and last message timestamp
CREATE OR REPLACE FUNCTION update_conversation_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations 
        SET 
            message_count = message_count + 1,
            last_message_at = NEW.created_at,
            updated_at = NOW()
        WHERE id = NEW.conversation_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to messages table
CREATE TRIGGER update_conversation_stats_trigger
    AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();

-- Procedure to get user's conversation statistics
CREATE OR REPLACE FUNCTION get_user_conversation_stats(p_user_id UUID)
RETURNS TABLE (
    total_conversations BIGINT,
    total_messages BIGINT,
    avg_messages_per_conversation DECIMAL(10,2),
    last_conversation_date TIMESTAMP WITH TIME ZONE,
    most_active_channel VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT c.id) as total_conversations,
        COUNT(m.id) as total_messages,
        CASE 
            WHEN COUNT(DISTINCT c.id) > 0 
            THEN ROUND(COUNT(m.id)::DECIMAL / COUNT(DISTINCT c.id), 2)
            ELSE 0 
        END as avg_messages_per_conversation,
        MAX(c.updated_at) as last_conversation_date,
        mode() WITHIN GROUP (ORDER BY c.channel_type) as most_active_channel
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id AND m.deleted_at IS NULL
    WHERE c.user_id = p_user_id
      AND c.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Example of how to create a backup function
CREATE OR REPLACE FUNCTION create_user_backup(p_user_id UUID, p_backup_type VARCHAR(50))
RETURNS UUID AS $$
DECLARE
    backup_id UUID;
BEGIN
    INSERT INTO backups (user_id, backup_type, status)
    VALUES (p_user_id, p_backup_type, 'pending')
    RETURNING id INTO backup_id;
    
    -- Here you would implement the actual backup logic
    -- This could involve:
    -- 1. Export user data to JSON/CSV
    -- 2. Create compressed archive
    -- 3. Store file information
    -- 4. Update backup status to 'completed'
    
    UPDATE backups 
    SET status = 'completed', completed_at = NOW()
    WHERE id = backup_id;
    
    RETURN backup_id;
END;
$$ LANGUAGE plpgsql;
