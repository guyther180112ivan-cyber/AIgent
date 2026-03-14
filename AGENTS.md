# AIgent Platform - Agent Coding Guidelines

## Project Overview

This is a full-stack AI agent platform with:
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- **Backend**: Python FastAPI, SQLAlchemy, PostgreSQL
- **Testing**: pytest with pytest-asyncio
- **Docker**: Docker Compose for full stack deployment

## Build Commands

### Frontend (Next.js)
```bash
cd frontend

# Development
npm run dev              # Start dev server on http://localhost:3000

# Production
npm run build            # Build for production
npm run start            # Start production server

# Linting & Type Checking
npm run lint             # Run ESLint
npm run type-check       # Run TypeScript type checking (tsc --noEmit)

# Single Test (if tests exist)
npm run test             # Run all tests (jest)
npm run test -- path/to/test.ts   # Run specific test file
```

### Backend (Python/FastAPI)
```bash
cd backend

# Using virtual environment (venv)
# Activate venv first: source venv/Scripts/activate (Windows)
# or: source venv/bin/activate (Linux/Mac)

# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with Python directly
python -m uvicorn app.main:app --reload

# Testing
pytest                              # Run all tests
pytest app/runtime/tests/           # Run specific test directory
pytest app/runtime/tests/test_agent_runtime.py::TestAgentRuntime::test_process_message_success  # Run single test
pytest -v                           # Verbose output
pytest -k "test_name"               # Run tests matching pattern
pytest --asyncio-mode=auto           # Handle async tests

# Linting (if installed)
ruff check .                        # Check Python files
ruff check --fix .                  # Check and fix
```

### Docker
```bash
# Start all services
docker-compose up -d

# Rebuild and start
docker-compose up -d --build

# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

## Code Style Guidelines

### TypeScript (Frontend)

#### Imports
- Use absolute imports with `@/` alias (configured in tsconfig.json)
- Order: external libraries → internal modules → local components/styles
- Example:
  ```typescript
  import React, { useState, useEffect } from 'react';
  import axios from 'axios';
  import { useQuery } from 'react-query';
  import { Button } from '@/components/ui/button';
  import { useAuthStore } from '@/stores/auth';
  import './styles.css';
  ```

#### Naming Conventions
- **Components**: PascalCase (e.g., `ChatWidget.tsx`, `UserProfile.tsx`)
- **Hooks**: camelCase starting with `use` (e.g., `useAuth`, `useChatMessages`)
- **Types/Interfaces**: PascalCase (e.g., `Message`, `User`, `Skill`)
- **Variables/Functions**: camelCase (e.g., `fetchTasks`, `isLoading`)
- **Constants**: SCREAMING_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`, `API_BASE_URL`)
- **Files**: kebab-case for non-component files (e.g., `api-client.ts`, `utils.ts`)

#### Types
- Always define explicit types for props, state, and function returns
- Use interfaces for object shapes
- Use type aliases for unions, intersections
- Enable strict null checks
- Example:
  ```typescript
  interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp?: Date;
  }

  type Tab = 'dashboard' | 'chat' | 'skills' | 'tools' | 'scheduler';
  ```

#### Component Structure
```typescript
'use client';

import React, { useState, useEffect, useRef } from 'react';

interface Props {
  title: string;
  onSubmit: (data: FormData) => void;
}

export default function MyComponent({ title, onSubmit }: Props) => {
  const [state, setState] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // effect logic
  }, []);

  const handleSubmit = () => {
    onSubmit(data);
  };

  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

#### Formatting
- Use 2 spaces for indentation
- Semicolons at end of statements
- Single quotes for strings
- Trailing commas in objects/arrays
- Max line length: 100 characters (soft limit)

### Python (Backend)

#### Imports
- Standard library → Third-party → Local application
- Use absolute imports from package root
- Example:
  ```python
  import asyncio
  import logging
  from typing import Optional, List
  
  from fastapi import FastAPI, Depends
  from sqlalchemy.orm import Session
  
  from app.core.config import settings
  from app.models import Agent, Skill
  from app.services.llm_service import LLMService
  ```

#### Naming Conventions
- **Classes**: PascalCase (e.g., `AgentRuntime`, `SchedulerService`)
- **Functions/Methods**: snake_case (e.g., `process_message`, `get_user_by_id`)
- **Variables**: snake_case (e.g., `user_id`, `is_active`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_TOKENS`, `DEFAULT_MODEL`)
- **Private methods**: prefix with underscore (e.g., `_load_agent_data`)
- **Async functions**: prefix with `async_` if not using async/await convention

#### Type Hints
- Use type hints for all function parameters and return types
- Use `Optional[X]` instead of `X | None`
- Use `List[X]`, `Dict[K, V]` from typing (or built-ins for Python 3.9+)
- Example:
  ```python
  from typing import Optional, List, Dict, Any
  
  async def process_message(
      user_id: str,
      conversation_id: str,
      message_content: str
  ) -> Dict[str, Any]:
      ...
  
  def get_agent_by_id(agent_id: str) -> Optional[Agent]:
      ...
  ```

#### Error Handling
- Use custom exception classes for domain errors
- Catch specific exceptions, not broad `Exception`
- Use proper HTTP status codes in FastAPI
- Example:
  ```python
  from fastapi import HTTPException, status
  
  class AgentRuntimeError(Exception):
      """Base exception for agent runtime errors."""
      pass
  
  class SkillLoadError(AgentRuntimeError):
      """Raised when skill loading fails."""
      pass
  
  async def get_agent(user_id: str) -> Agent:
      agent = await db.query(Agent).filter(Agent.id == user_id).first()
      if not agent:
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail=f"Agent with id {user_id} not found"
          )
      return agent
  ```

#### SQLAlchemy Models
```python
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="agent")
```

### Testing Conventions

#### Python/pytest
- Test files: `test_*.py` or `*_test.py`
- Test classes: `TestClassName`
- Test methods: `test_method_name`
- Use fixtures for setup/teardown
- Use `pytest.mark.asyncio` for async tests
- Example:
  ```python
  import pytest
  from unittest.mock import Mock, AsyncMock
  
  @pytest.fixture
  def mock_db():
      return Mock()
  
  @pytest.fixture
  def agent_runtime(mock_db):
      return AgentRuntime(mock_db)
  
  @pytest.mark.asyncio
  async def test_process_message_success(agent_runtime, mock_db):
      result = await agent_runtime.process_message(...)
      assert result["response"] == "expected"
  ```

#### Test Commands
```bash
# Run all tests with verbose output
pytest -v

# Run specific test file
pytest app/runtime/tests/test_agent_runtime.py

# Run specific test class
pytest app/runtime/tests/test_agent_runtime.py::TestAgentRuntime

# Run specific test method
pytest app/runtime/tests/test_agent_runtime.py::TestAgentRuntime::test_process_message_success

# Run tests matching pattern
pytest -k "agent_runtime"

# Run with coverage (if installed)
pytest --cov=app --cov-report=html
```

### General Best Practices

1. **Environment Variables**: Never commit secrets to version control
   - Use `.env.local` for frontend ( Next.js loads it automatically)
   - Use `.env` or environment variables for backend
   - Reference `docker-compose.yml` for required variables

2. **API Patterns**: 
   - RESTful endpoints for CRUD operations
   - Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
   - Return consistent response formats

3. **Logging**:
   - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
   - Include context in log messages
   - Example: `logger.info(f"Processing message for user {user_id}")`

4. **Database**:
   - Use migrations (Alembic) for schema changes
   - Never bypass SQLAlchemy for raw queries unless necessary
   - Use transactions for multi-step operations

5. **Async/Await**:
   - Use async/await for I/O operations
   - Don't block the event loop with synchronous operations
   - Use `asyncio.gather()` for concurrent operations

## Key File Locations

- Frontend entry: `frontend/app/page.tsx`
- Backend entry: `backend/app/main.py`
- Database models: `backend/app/models/`
- API routes: `backend/app/api/`
- Tests: `backend/app/*/tests/`
- Configuration: `backend/app/core/config.py`

## Useful Commands Summary

```bash
# Frontend
npm run dev
npm run build
npm run lint
npm run type-check

# Backend  
python -m uvicorn app.main:app --reload
pytest -v

# Docker
docker-compose up -d
docker-compose logs -f

# Database (if needed)
# PostgreSQL runs on port 5432
# Redis runs on port 6379
```
