-- ====================================================================
-- AIgent v3 — Supabase PostgreSQL Schema
-- Принцип: «Добавляй — не меняй»
-- Схема разделена на независимые секции (модули)
-- ====================================================================

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "vector"; -- Раскомментировать для pgvector (RAG)

-- ====================================================================
-- CORE: Агенты
-- ====================================================================
CREATE TABLE IF NOT EXISTS agents (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  description TEXT,
  system_prompt TEXT NOT NULL DEFAULT 'You are a helpful AI assistant.',
  model       TEXT NOT NULL DEFAULT 'openai/gpt-4o-mini',
  avatar_url  TEXT,
  is_active   BOOLEAN NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS: пользователь видит только своих агентов
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "agents_user_policy" ON agents
  USING (auth.uid() = user_id);

-- ====================================================================
-- CORE: Разговоры
-- ====================================================================
CREATE TABLE IF NOT EXISTS conversations (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id    UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title       TEXT NOT NULL DEFAULT 'Новый чат',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "conversations_user_policy" ON conversations
  USING (auth.uid() = user_id);

-- ====================================================================
-- CORE: Сообщения
-- ====================================================================
CREATE TABLE IF NOT EXISTS messages (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
  content         TEXT NOT NULL,
  metadata        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "messages_user_policy" ON messages
  USING (
    EXISTS (
      SELECT 1 FROM conversations c
      WHERE c.id = messages.conversation_id
        AND c.user_id = auth.uid()
    )
  );

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- ====================================================================
-- MODULE: Skills
-- ====================================================================
CREATE TABLE IF NOT EXISTS skills (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name            TEXT NOT NULL,
  description     TEXT,
  prompt_template TEXT NOT NULL DEFAULT '',
  parameters      JSONB NOT NULL DEFAULT '[]',
  type            TEXT NOT NULL DEFAULT 'prompt' CHECK (type IN ('prompt', 'anthropic')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_skills (
  agent_id  UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  skill_id  UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  config    JSONB DEFAULT '{}',
  PRIMARY KEY (agent_id, skill_id)
);

ALTER TABLE agent_skills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "agent_skills_user_policy" ON agent_skills
  USING (
    EXISTS (
      SELECT 1 FROM agents a
      WHERE a.id = agent_skills.agent_id
        AND a.user_id = auth.uid()
    )
  );

-- ====================================================================
-- MODULE: Tools
-- ====================================================================
CREATE TABLE IF NOT EXISTS tools (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name         TEXT NOT NULL,
  description  TEXT,
  type         TEXT NOT NULL DEFAULT 'http' CHECK (type IN ('http', 'toolhouse', 'custom')),
  config       JSONB NOT NULL DEFAULT '{}',
  input_schema JSONB NOT NULL DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_tools (
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  tool_id  UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
  config   JSONB DEFAULT '{}',
  PRIMARY KEY (agent_id, tool_id)
);

ALTER TABLE agent_tools ENABLE ROW LEVEL SECURITY;
CREATE POLICY "agent_tools_user_policy" ON agent_tools
  USING (
    EXISTS (
      SELECT 1 FROM agents a
      WHERE a.id = agent_tools.agent_id
        AND a.user_id = auth.uid()
    )
  );

-- ====================================================================
-- MODULE: Long-term Memory
-- ====================================================================
CREATE TABLE IF NOT EXISTS memory_items (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  agent_id   UUID REFERENCES agents(id) ON DELETE SET NULL,
  content    TEXT NOT NULL,
  importance INTEGER NOT NULL DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
  tags       TEXT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ
);

ALTER TABLE memory_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "memory_items_user_policy" ON memory_items
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_memory_items_user_id ON memory_items(user_id);

-- ====================================================================
-- MODULE: RAG
-- ====================================================================
CREATE TABLE IF NOT EXISTS rag_documents (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  content    TEXT NOT NULL,
  source     TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "rag_documents_user_policy" ON rag_documents
  USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS rag_chunks (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
  content     TEXT NOT NULL,
  chunk_index INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
  -- embedding   vector(1536)  -- Раскомментировать для pgvector
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_document_id ON rag_chunks(document_id);

-- Полнотекстовый поиск
CREATE INDEX IF NOT EXISTS idx_rag_chunks_content_fts
  ON rag_chunks USING gin(to_tsvector('russian', content));

-- ====================================================================
-- MODULE: Scheduler
-- ====================================================================
CREATE TABLE IF NOT EXISTS scheduled_tasks (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id    UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  description TEXT,
  cron_expr   TEXT NOT NULL,
  action      JSONB NOT NULL DEFAULT '{}',
  is_active   BOOLEAN NOT NULL DEFAULT true,
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "scheduled_tasks_user_policy" ON scheduled_tasks
  USING (auth.uid() = user_id);

-- ====================================================================
-- MODULE: Reminders
-- ====================================================================
CREATE TABLE IF NOT EXISTS reminders (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  agent_id   UUID REFERENCES agents(id) ON DELETE SET NULL,
  text       TEXT NOT NULL,
  remind_at  TIMESTAMPTZ NOT NULL,
  channel    TEXT NOT NULL DEFAULT 'web' CHECK (channel IN ('web', 'telegram', 'email')),
  is_sent    BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "reminders_user_policy" ON reminders
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at);
CREATE INDEX IF NOT EXISTS idx_reminders_is_sent ON reminders(is_sent);

-- ====================================================================
-- MODULE: Telegram
-- ====================================================================
CREATE TABLE IF NOT EXISTS telegram_links (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  telegram_id TEXT NOT NULL UNIQUE,
  username    TEXT,
  first_name  TEXT,
  linked_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE telegram_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY "telegram_links_user_policy" ON telegram_links
  USING (auth.uid() = user_id);

-- ====================================================================
-- Триггер: updated_at
-- ====================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at
  BEFORE UPDATE ON agents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at
  BEFORE UPDATE ON conversations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
