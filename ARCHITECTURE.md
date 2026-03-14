# Архитектура AIgent Platform

> Документация архитектуры системы | Версия 2.0

## Обзор

AIgent Platform построена на модульной архитектуре с четким разделением ответственности между компонентами. Система состоит из трех основных частей:

1. **Frontend** - Next.js приложение (React + TypeScript)
2. **Backend** - FastAPI сервис (Python)
3. **Telegram Bot** - Интегрированный бот на python-telegram-bot

## Диаграмма компонентов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              КЛИЕНТСКИЙ СЛОЙ                                │
├──────────────────────────┬─────────────────────┬────────────────────────────┤
│      Веб-браузер         │    Telegram App     │     API Клиенты            │
│  • React интерфейс       │  • Мобильное        │  • curl                    │
│  • localhost:3000        │    приложение       │  • Postman                 │
│  • Прямой доступ к       │  • Desktop клиент   │  • Кастомные               │
│    OpenRouter API        │  • Web версия       │    интеграции              │
└───────────┬──────────────┴──────────┬──────────┴──────────────┬─────────────┘
            │                         │                         │
            │ HTTP                    │ HTTPS (Telegram API)    │ HTTP
            ▼                         │                         │
┌─────────────────────────────────────┴─────────────────────────┴─────────────┐
│                         BACKEND LAYER (FastAPI)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      API Layer (Routers)                             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │  │
│  │  │ /auth    │ │ /agents  │ │ /skills  │ │ /tools   │ │ /chat    │    │  │
│  │  │          │ │          │ │          │ │          │ │          │    │  │
│  │  │• login   │ │• list   │ │• list   │ │• list   │ │• send   │    │  │
│  │  │• register│ │• create │ │• create │ │• create │ │• history│    │  │
│  │  │• telegram│ │• update │ │• update │ │• update │ │         │    │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Services Layer                                    │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │  │
│  │  │ LLMService   │ │ AuthService  │ │ PromptGen    │                  │  │
│  │  │              │ │              │ │              │                  │  │
│  │  │• OpenRouter  │ │• JWT         │ │• Prompts     │                  │  │
│  │  │• Models      │ │• Password    │ │• Templates   │                  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Runtime Layer                                     │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │  │
│  │  │AgentRuntime  │ │ToolExecutor  │ │PromptComposer│                  │  │
│  │  │              │ │              │ │              │                  │  │
│  │  │• Execute     │ │• HTTP tools  │ │• Jinja2      │                  │  │
│  │  │• Context     │ │• Python      │ │• Variables   │                  │  │
│  │  │• Memory      │ │• Validation  │ │• Composition │                  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Data Layer                                        │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────────┐  │  │
│  │  │ SQLAlchemy   │ │   Models     │ │     Database                 │  │  │
│  │  │              │ │              │ │                              │  │  │
│  │  │• ORM         │ │• User        │ │  SQLite (dev)                │  │  │
│  │  │• Sessions    │ │• Agent       │ │  PostgreSQL (prod)           │  │  │
│  │  │• Migrations  │ │• Skill       │ │                              │  │  │
│  │  └──────────────┘ │• Tool        │ └──────────────────────────────┘  │  │
│  │                   │• Conversation│                                   │  │
│  │                   └──────────────┘                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Telegram Bot (background)                         │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │  │
│  │  │ Bot Handler  │ │ User Linking │ │ OpenRouter   │                  │  │
│  │  │              │ │              │ │ Integration  │                  │  │
│  │  │• /start      │ │• /link       │ │• Direct API  │                  │  │
│  │  │• /link       │ │• Persistence │ │• Context     │                  │  │
│  │  │• Messages    │ │• JSON file   │ │• Streaming   │                  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ВНЕШНИЕ СЕРВИСЫ                                   │
├─────────────────────────────────┬───────────────────────────────────────────┤
│        OpenRouter API           │          Telegram API                     │
│                                 │                                           │
│  • 200+ LLM моделей            │  • Bot Platform                           │
│  • Unified API                 │  • Updates (polling)                      │
│  • Free tier available         │  • Send/Receive messages                  │
│  • Context support             │  • Media support                          │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

## Поток данных

### 1. Веб-интерфейс → OpenRouter (Frontend прямой доступ)

```
Пользователь → Browser → Next.js App → OpenRouter API
                              │
                              ├─> UI Components (React)
                              ├─> State Management (Context)
                              └─> HTTP Client (fetch/axios)
```

**Преимущества:**
- Минимальная задержка (нет proxy через backend)
- Масштабируемость (backend не нагружается LLM запросами)
- Простота архитектуры

### 2. Telegram → OpenRouter (Через backend бота)

```
Telegram User → Telegram API → Bot Handler → OpenRouter API
                                        │
                                        ├─> User Linking
                                        ├─> Context Management
                                        └─> Response Formatting
```

**Особенности:**
- Персистентность через JSON-файл
- Контекст диалога сохраняется
- Одноразовая привязка пользователя

### 3. Backend API (CRUD операции)

```
Клиент → FastAPI Router → SQLAlchemy → SQLite/PostgreSQL
            │
            ├─> Pydantic Validation
            ├─> JWT Authentication
            └─> Error Handling
```

## Модули Backend

### Core Module (`app/core/`)

**config.py**
```python
class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    TELEGRAM_BOT_TOKEN: str
    DEFAULT_MODEL: str = "openrouter/free"
    DATABASE_URL: str = "sqlite:///./aigent.db"
```

**database.py**
```python
# Cross-database UUID поддержка
class GUID(TypeDecorator):
    """PostgreSQL UUID / SQLite String адаптер"""
    
engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(engine)
```

### Models (`app/models/`)

**User**
- id (UUID)
- email (unique)
- hashed_password
- telegram_id (optional)
- is_active

**Agent**
- id (UUID)
- name
- system_prompt
- model
- owner_id
- skills (relationship)
- tools (relationship)

**Skill**
- id (UUID)
- name
- description
- prompt_template (Jinja2)
- parameters (JSON)

**Tool**
- id (UUID)
- name
- description
- type (http, python)
- config (JSON)
- input_schema (JSON Schema)

### API Layer (`app/api/`)

**auth.py**
```python
@router.post("/register")
async def register(user: UserCreate) -> Token

@router.post("/login")
async def login(credentials: LoginRequest) -> Token

@router.post("/telegram")
async def telegram_auth(data: TelegramAuth) -> Token
```

**agents.py**
```python
@router.get("/")
async def list_agents() -> List[AgentResponse]

@router.post("/")
async def create_agent(agent: AgentCreate) -> AgentResponse

@router.get("/{agent_id}")
async def get_agent(agent_id: UUID) -> AgentResponse

@router.put("/{agent_id}")
async def update_agent(agent_id: UUID, agent: AgentUpdate) -> AgentResponse

@router.delete("/{agent_id}")
async def delete_agent(agent_id: UUID) -> None
```

### Runtime (`app/runtime/`)

**AgentRuntime**
```python
class AgentRuntime:
    def __init__(self, agent_id: UUID, db: Session):
        self.agent = get_agent(agent_id)
        self.llm = LLMService()
        self.tools = ToolExecutor()
        self.prompt = PromptComposer()
    
    async def execute(self, message: str, context: dict) -> str:
        # 1. Compose prompt with context
        # 2. Load skills
        # 3. Execute LLM call
        # 4. Handle tool calls if any
        # 5. Return response
```

**ToolExecutor**
```python
class ToolExecutor:
    def register_tool(self, tool: BaseTool) -> None
    def execute_tool(self, tool_name: str, params: dict) -> Any
    def list_tools(self) -> List[str]
```

### Telegram Bot (`telegram_bot.py`)

```python
class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self.linked_users = self.load_linked_users()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Приветственное сообщение
    
    async def link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Привязка Telegram ID к пользователю
        # Одноразовая операция
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Обработка текстовых сообщений
        # Получение контекста из linked_users
        # Вызов OpenRouter API
        # Отправка ответа
```

## Frontend Архитектура

### Структура (App Router)

```
frontend/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Главная страница (чат)
│   ├── layout.tsx         # Корневой layout
│   └── globals.css        # Глобальные стили
├── src/
│   ├── components/        # React компоненты
│   │   ├── layout/       # Layout компоненты
│   │   │   ├── Header.tsx
│   │   │   └── Sidebar.tsx
│   │   └── chat/         # Компоненты чата
│   │       ├── ChatWindow.tsx
│   │       ├── MessageList.tsx
│   │       └── InputArea.tsx
│   ├── pages/            # Страницы
│   │   ├── DashboardPage.tsx
│   │   ├── SkillsPage.tsx
│   │   └── ToolsPage.tsx
│   └── services/         # API клиенты
│       └── api.ts
```

### Компоненты

**ChatPage (app/page.tsx)**
```typescript
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [model, setModel] = useState('openrouter/free')
  
  const sendMessage = async () => {
    // Прямой запрос к OpenRouter API
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model,
        messages: [...messages, { role: 'user', content: input }]
      })
    })
    // Обработка ответа...
  }
}
```

## База данных

### Схема (SQLite/PostgreSQL)

```sql
-- Users
CREATE TABLE users (
    id GUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    telegram_id VARCHAR UNIQUE,
    is_active BOOLEAN DEFAULT true
);

-- Agents
CREATE TABLE agents (
    id GUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    system_prompt TEXT,
    model VARCHAR DEFAULT 'openrouter/free',
    owner_id GUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Skills
CREATE TABLE skills (
    id GUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    prompt_template TEXT,
    parameters JSON
);

-- Agent-Skill связь
CREATE TABLE agent_skills (
    agent_id GUID REFERENCES agents(id),
    skill_id GUID REFERENCES skills(id),
    config JSON,
    PRIMARY KEY (agent_id, skill_id)
);

-- Tools
CREATE TABLE tools (
    id GUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    type VARCHAR CHECK (type IN ('http', 'python')),
    config JSON,
    input_schema JSON
);

-- Agent-Tool связь
CREATE TABLE agent_tools (
    agent_id GUID REFERENCES agents(id),
    tool_id GUID REFERENCES tools(id),
    config JSON,
    PRIMARY KEY (agent_id, tool_id)
);

-- Conversations
CREATE TABLE conversations (
    id GUID PRIMARY KEY,
    agent_id GUID REFERENCES agents(id),
    user_id GUID REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id GUID PRIMARY KEY,
    conversation_id GUID REFERENCES conversations(id),
    role VARCHAR CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Конфигурация

### Переменные окружения (`.env`)

```bash
# Обязательные
OPENROUTER_API_KEY=sk-or-v1-xxx
TELEGRAM_BOT_TOKEN=xxx:xxx

# Опциональные
DEFAULT_MODEL=openrouter/free
DATABASE_URL=sqlite:///./aigent.db
DEBUG=true
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Паттерны проектирования

### 1. Repository Pattern
```python
class AgentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, id: UUID) -> Agent:
        return self.db.query(Agent).filter(Agent.id == id).first()
    
    def create(self, agent: AgentCreate) -> Agent:
        db_agent = Agent(**agent.dict())
        self.db.add(db_agent)
        self.db.commit()
        return db_agent
```

### 2. Service Layer
```python
class LLMService:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.api_key = settings.OPENROUTER_API_KEY
    
    async def chat_completion(
        self, 
        messages: List[Message], 
        model: str = None
    ) -> str:
        response = await self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": model or settings.DEFAULT_MODEL, "messages": messages}
        )
        return response.json()["choices"][0]["message"]["content"]
```

### 3. Dependency Injection (FastAPI)
```python
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    return await verify_token(token, db)

@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await AgentRepository(db).get_by_owner(user.id)
```

## Масштабирование

### Горизонтальное масштабирование

```
Load Balancer
     │
     ├─> Backend Instance 1 (Telegram Bot)
     ├─> Backend Instance 2 (API only)
     └─> Backend Instance 3 (API only)
     
PostgreSQL (Primary-Replica)
```

**Примечание**: Telegram бот должен быть запущен только на одном инстансе.

### Кэширование

```python
# Redis для кэширования
@cache(ttl=3600)
async def get_agent_skills(agent_id: UUID) -> List[Skill]:
    return await repository.get_skills(agent_id)
```

## Безопасность

### Аутентификация
- JWT токены с expiration
- bcrypt для хеширования паролей
- HTTPS в production

### Авторизация
- Role-based access control (RBAC)
- Resource ownership verification

### Валидация
- Pydantic модели для всех входных данных
- SQL injection защита через ORM
- XSS защита через React escaping

## Мониторинг

### Health Checks
```
GET /health
Response: {
    "status": "healthy",
    "telegram_bot": "running",
    "database": "connected"
}
```

### Логирование
- Структурированные JSON логи
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs для tracing

## Заключение

Архитектура AIgent Platform разработана для:
- **Гибкости**: Легко добавлять новые интеграции
- **Масштабируемости**: Горизонтальное масштабирование компонентов
- **Поддерживаемости**: Четкое разделение ответственности
- **Безопасности**: Многоуровневая защита данных
