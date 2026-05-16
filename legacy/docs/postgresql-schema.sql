-- PostgreSQL Schema for AIgent Platform
-- One AI agent per user with skills and tools

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- Agents table (one agent per user)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL DEFAULT 'You are a helpful AI assistant.',
    model_name VARCHAR(100) NOT NULL DEFAULT 'gpt-3.5-turbo',
    configuration JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- Skills table (available skills in the system)
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    system_prompt_template TEXT NOT NULL,
    default_config JSONB NOT NULL DEFAULT '{}',
    is_builtin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- User Skills junction table (skills assigned to user's agent)
CREATE TABLE user_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    config JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    UNIQUE(user_id, skill_id)
);

-- Tools table (available tools in the system)
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    function_schema JSONB NOT NULL,
    default_config JSONB NOT NULL DEFAULT '{}',
    is_builtin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- User Tools junction table (tools assigned to user's agent)
CREATE TABLE user_tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    config JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    UNIQUE(user_id, tool_id)
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL, -- 'web', 'telegram', 'voice'
    channel_id VARCHAR(255) NOT NULL, -- chat_id, session_id, etc.
    title VARCHAR(255),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

-- Tool Calls table (function calls made by agent)
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB NOT NULL,
    result TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

-- Telegram Links table (user-telegram account connections)
CREATE TABLE telegram_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_user_id BIGINT NOT NULL,
    telegram_username VARCHAR(255),
    telegram_chat_id BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    UNIQUE(user_id, telegram_user_id),
    UNIQUE(telegram_chat_id)
);

-- Voice Settings table (user voice preferences)
CREATE TABLE voice_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stt_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    tts_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    stt_config JSONB NOT NULL DEFAULT '{}',
    tts_config JSONB NOT NULL DEFAULT '{}',
    voice_id VARCHAR(100), -- Preferred voice ID
    language_code VARCHAR(10) DEFAULT 'en-US',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

-- Sessions table (for authentication)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- Create indexes for performance
-- Users indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;

-- Agents indexes
CREATE INDEX idx_agents_user_id ON agents(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_active ON agents(is_active) WHERE deleted_at IS NULL;

-- Skills indexes
CREATE INDEX idx_skills_name ON skills(name) WHERE deleted_at IS NULL;
CREATE INDEX idx_skills_slug ON skills(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_skills_builtin ON skills(is_builtin) WHERE deleted_at IS NULL;
CREATE INDEX idx_skills_active ON skills(is_active) WHERE deleted_at IS NULL;

-- User Skills indexes
CREATE INDEX idx_user_skills_user_id ON user_skills(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_skills_skill_id ON user_skills(skill_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_skills_enabled ON user_skills(is_enabled) WHERE deleted_at IS NULL;

-- Tools indexes
CREATE INDEX idx_tools_name ON tools(name) WHERE deleted_at IS NULL;
CREATE INDEX idx_tools_slug ON tools(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_tools_builtin ON tools(is_builtin) WHERE deleted_at IS NULL;
CREATE INDEX idx_tools_active ON tools(is_active) WHERE deleted_at IS NULL;

-- User Tools indexes
CREATE INDEX idx_user_tools_user_id ON user_tools(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_tools_tool_id ON user_tools(tool_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_tools_enabled ON user_tools(is_enabled) WHERE deleted_at IS NULL;

-- Conversations indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_channel ON conversations(channel_type, channel_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC) WHERE deleted_at IS NULL;

-- Messages indexes
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_messages_created_at ON messages(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_messages_role ON messages(role) WHERE deleted_at IS NULL;

-- Tool Calls indexes
CREATE INDEX idx_tool_calls_message_id ON tool_calls(message_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tool_calls_status ON tool_calls(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name) WHERE deleted_at IS NULL;

-- Telegram Links indexes
CREATE INDEX idx_telegram_links_user_id ON telegram_links(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_telegram_links_telegram_user_id ON telegram_links(telegram_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_telegram_links_chat_id ON telegram_links(telegram_chat_id) WHERE deleted_at IS NULL;

-- Voice Settings indexes
CREATE INDEX idx_voice_settings_user_id ON voice_settings(user_id) WHERE deleted_at IS NULL;

-- Sessions indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_skills_updated_at BEFORE UPDATE ON user_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tools_updated_at BEFORE UPDATE ON tools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_tools_updated_at BEFORE UPDATE ON user_tools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_telegram_links_updated_at BEFORE UPDATE ON telegram_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_voice_settings_updated_at BEFORE UPDATE ON voice_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create constraints and checks
-- One agent per user constraint
ALTER TABLE agents ADD CONSTRAINT one_agent_per_user 
UNIQUE (user_id) WHERE deleted_at IS NULL;

-- Check constraints for enums
ALTER TABLE messages ADD CONSTRAINT check_message_role 
CHECK (role IN ('user', 'assistant', 'system'));

ALTER TABLE conversations ADD CONSTRAINT check_channel_type 
CHECK (channel_type IN ('web', 'telegram', 'voice'));

ALTER TABLE tool_calls ADD CONSTRAINT check_tool_call_status 
CHECK (status IN ('pending', 'completed', 'failed'));

ALTER TABLE voice_settings ADD CONSTRAINT check_stt_provider 
CHECK (stt_provider IN ('openai', 'google', 'azure', 'aws'));

ALTER TABLE voice_settings ADD CONSTRAINT check_tts_provider 
CHECK (tts_provider IN ('openai', 'google', 'azure', 'aws'));

-- Create views for commonly accessed data
CREATE VIEW active_users AS
SELECT * FROM users 
WHERE deleted_at IS NULL AND is_active = TRUE;

CREATE VIEW user_agents AS
SELECT u.id as user_id, u.username, u.name, a.*
FROM users u
JOIN agents a ON u.id = a.user_id
WHERE u.deleted_at IS NULL AND a.deleted_at IS NULL;

CREATE VIEW user_enabled_skills AS
SELECT u.id as user_id, u.username, s.id as skill_id, s.name, s.description, us.config
FROM users u
JOIN user_skills us ON u.id = us.user_id
JOIN skills s ON us.skill_id = s.id
WHERE u.deleted_at IS NULL 
  AND us.deleted_at IS NULL 
  AND s.deleted_at IS NULL
  AND us.is_enabled = TRUE
  AND s.is_active = TRUE;

CREATE VIEW user_enabled_tools AS
SELECT u.id as user_id, u.username, t.id as tool_id, t.name, t.description, t.function_schema, ut.config
FROM users u
JOIN user_tools ut ON u.id = ut.user_id
JOIN tools t ON ut.tool_id = t.id
WHERE u.deleted_at IS NULL 
  AND ut.deleted_at IS NULL 
  AND t.deleted_at IS NULL
  AND ut.is_enabled = TRUE
  AND t.is_active = TRUE;

-- Insert some default built-in skills
INSERT INTO skills (name, slug, description, system_prompt_template, is_builtin) VALUES
('General Assistant', 'general-assistant', 'Basic conversational AI assistant capabilities', 'You are a helpful AI assistant. Be friendly, professional, and helpful in your responses.', TRUE),
('Code Helper', 'code-helper', 'Programming and coding assistance', 'You are a coding expert. Help with programming questions, code review, debugging, and best practices. Provide clear, well-commented code examples.', TRUE),
('Creative Writer', 'creative-writer', 'Creative writing and storytelling', 'You are a creative writer. Help with storytelling, creative writing, poetry, and content creation. Be imaginative and engaging.', TRUE),
('Data Analyst', 'data-analyst', 'Data analysis and interpretation', 'You are a data analyst. Help with data interpretation, analysis, and visualization. Be precise and methodical in your approach.', TRUE);

-- Insert some default built-in tools
INSERT INTO tools (name, slug, description, function_schema, is_builtin) VALUES
('Web Search', 'web-search', 'Search the web for information', '{
  "name": "web_search",
  "description": "Search the web for current information",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "num_results": {
        "type": "integer",
        "description": "Number of results to return",
        "default": 5
      }
    },
    "required": ["query"]
  }
}', TRUE),
('Calculator', 'calculator', 'Perform mathematical calculations', '{
  "name": "calculator",
  "description": "Perform mathematical calculations",
  "parameters": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "description": "Mathematical expression to evaluate"
      }
    },
    "required": ["expression"]
  }
}', TRUE),
('Weather', 'weather', 'Get current weather information', '{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or coordinates"
      },
      "units": {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "default": "celsius"
      }
    },
    "required": ["location"]
  }
}', TRUE);
