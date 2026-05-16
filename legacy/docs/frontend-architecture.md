# Frontend Architecture

## Overview

Современный минималистичный frontend для платформы с одним ИИ-агентом на пользователя. Вдохновлен дизайном американских стартапов - чистый, функциональный, сфокусированный на пользовательском опыте.

## Стек технологий

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: Custom components с shadcn/ui
- **Icons**: Heroicons
- **State Management**: React hooks + Context API
- **Routing**: Next.js App Router

## Архитектура

### Layout System

```
AppLayout
├── Header (навигация, профиль, уведомления)
├── Sidebar (основная навигация)
└── Main Content (динамический контент)
```

**Компоненты:**
- `AppLayout` - основной лейаут приложения
- `Header` - верхняя панель с логотипом, профилем, уведомлениями
- `Sidebar` - боковая навигация с активными состояниями

### Страницы

#### 1. Login Page (`/login`)
- Минималистичная форма входа
- Социальные логины (Google, GitHub)
- Ссылка на регистрацию
- Восстановление пароля

**UX Flow:**
```
Email/Password → Валидация → Dashboard
или
Social Login → OAuth → Dashboard
```

#### 2. Dashboard (`/dashboard`)
- Обзор статистики агента
- Быстрые действия
- Последняя активность
- Статус агента

**Компоненты:**
- Статистические карточки (conversations, skills, tools, usage)
- Список последних активностей
- Кнопки быстрых действий
- Статус агента в реальном времени

#### 3. Skills Page (`/skills`)
- Управление навыками агента
- Включение/отключение навыков
- Настройка уровня владения
- Поиск и фильтрация

**UX Flow:**
```
Список навыков → Фильтрация → Детали → Настройки → Сохранение
```

**Компоненты:**
- Карточки навыков с toggle switches
- Звёздный рейтинг для уровня владения
- Теги и категории
- Конфигурация навыков

#### 4. Tools Page (`/tools`)
- Управление инструментами
- Включение/отключение интеграций
- Настройка API ключей
- Статус инструментов

**UX Flow:**
```
Список инструментов → Выбор → Конфигурация → Тестирование → Активация
```

**Компоненты:**
- Карточки инструментов с индикаторами статуса
- Формы конфигурации
- Тестовые запросы
- Лог использования

#### 5. Chat Page (`/chat`)
- Основной интерфейс общения с агентом
- Поддержка текста и голоса
- История диалогов
- Real-time индикаторы

**UX Flow:**
```
Сообщение → Обработка → Ответ → История
или
Голос → STT → Обработка → TTS → Ответ
```

**Компоненты:**
- Сообщения с временными метками
- Индикаторы состояния (listening/thinking/speaking)
- Голосовые кнопки с визуализацией
- Настройки чата

## Дизайн система

### Цветовая палитра

```css
/* Primary */
--primary-50: #eff6ff
--primary-500: #3b82f6
--primary-600: #2563eb
--primary-700: #1d4ed8

/* Neutral */
--gray-50: #f9fafb
--gray-100: #f3f4f6
--gray-500: #6b7280
--gray-900: #111827

/* Status */
--success: #10b981
--warning: #f59e0b
--error: #ef4444
```

### Типографика

```css
/* Заголовки */
text-2xl font-light text-gray-900  /* H1 */
text-lg font-medium text-gray-900   /* H2 */
text-sm font-medium text-gray-700   /* H3 */

/* Текст */
text-sm text-gray-600               /* Body */
text-xs text-gray-500               /* Caption */
```

### Компоненты

#### Buttons
```css
/* Primary */
bg-blue-600 text-white hover:bg-blue-700

/* Secondary */
bg-gray-100 text-gray-700 hover:bg-gray-200

/* Ghost */
text-gray-600 hover:bg-gray-100
```

#### Cards
```css
bg-white rounded-lg shadow-sm border border-gray-200
```

#### Forms
```css
border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500
```

## UX Flow

### Аутентификация
```
Landing → Login → Dashboard
```

### Основной workflow
```
Dashboard → Skills/Tools → Chat → Настройки
```

### Управление навыками
```
Skills Page → Выбор навыка → Toggle → Профiciency → Сохранение
```

### Общение с агентом
```
Chat Page → Текст/Голос → Обработка → Ответ → История
```

## Voice UX

### Состояния голосового интерфейса
1. **Ready** - готов к записи
2. **Listening** - запись голоса (красная индикация)
3. **Thinking** - обработка запроса (желтая индикация)
4. **Speaking** - воспроизведение ответа (зеленая индикация)

### Voice Components
- Кнопка записи с визуализацией
- Индикаторы состояния в реальном времени
- Waveform анимация для записи
- TTS кнопки для ответов

### Voice Flow
```
Нажать микрофон → Recording → Отпустить → STT → Отправить → Обработка → TTS → Воспроизведение
```

## Responsive Design

### Breakpoints
```css
sm: 640px   /* Mobile */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large */
```

### Адаптация
- **Mobile**: скрытый sidebar, bottom navigation
- **Tablet**: collapsible sidebar
- **Desktop**: полный лейаут

## Performance

### Оптимизации
1. **Code splitting** - динамическая загрузка страниц
2. **Image optimization** - Next.js Image component
3. **Lazy loading** - для тяжелых компонентов
4. **Caching** - API responses и статические данные

### Метрики
- **FCP** < 1.5s
- **LCP** < 2.5s
- **FID** < 100ms
- **CLS** < 0.1

## Accessibility

### WCAG 2.1 AA
- Семантическая HTML разметка
- ARIA labels и landmarks
- Keyboard navigation
- Color contrast ratio > 4.5:1
- Focus indicators

### Features
- Screen reader поддержка
- Voice navigation
- High contrast mode
- Reduced motion

## State Management

### Local State
```typescript
// React hooks для компонентного состояния
const [messages, setMessages] = useState<Message[]>([]);
const [isLoading, setIsLoading] = useState(false);
```

### Global State
```typescript
// Context для пользовательских данных
const UserContext = createContext<UserState>();
```

### Server State
```typescript
// API calls с React Query/SWR
const { data: skills, isLoading } = useSkills();
```

## Error Handling

### Error Boundaries
```typescript
class ErrorBoundary extends Component {
  // Глобальная обработка ошибок
}
```

### User Feedback
- Toast notifications для ошибок
- Skeleton loaders для загрузки
- Graceful degradation для fallback

## Testing

### Unit Tests
- Компонентные тесты с React Testing Library
- Mock API responses
- Coverage > 80%

### E2E Tests
- Playwright для critical paths
- Mobile responsiveness
- Voice interaction flows

## Deployment

### Environment
```bash
# Production
NEXT_PUBLIC_API_URL=https://api.aigent.com
NEXT_PUBLIC_WS_URL=wss://api.aigent.com

# Development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Build Process
```bash
# Build
npm run build

# Start
npm run start
```

## Future Enhancements

### PWA Features
- Service Worker для оффлайн режима
- Push notifications для новых сообщений
- App installation prompt

### Advanced Voice
- Voice commands для навигации
- Ambient listening mode
- Voice biometrics для security

### AI Features
- Smart suggestions в чате
- Auto-completion для команд
- Contextual help tooltips

Фронтенд обеспечивает современный, интуитивный интерфейс для управления ИИ-агентом с фокусом на минимализм и пользовательский опыт.
