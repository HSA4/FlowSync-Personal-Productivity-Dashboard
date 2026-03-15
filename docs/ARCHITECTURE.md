# FlowSync - System Architecture

**Last Updated**: 2025-01-15

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   React +    │  │  Tailwind    │  │  React       │      │
│  │   Vite       │  │  CSS         │  │  Router      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   FastAPI    │  │   Pydantic   │  │   Uvicorn    │      │
│  │   (REST)     │  │  (Models)    │  │  (Server)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    MySQL     │  │    Redis     │  │  File System │      │
│  │ (Primary DB) │  │   (Cache)    │  │   (Logs)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     External APIs                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Todoist     │  │ Google       │  │   Gmail      │      │
│  │  API         │  │  Calendar    │  │   API        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
FlowSync-Personal-Productivity-Dashboard/
├── .github/
│   └── workflows/
│       └── claude-continue.yml    # Auto-trigger workflow
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── models/                    # Pydantic models
│   ├── services/                  # Business logic
│   ├── api/                       # API routes
│   └── config/                    # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── services/              # API clients
│   │   ├── hooks/                 # Custom hooks
│   │   └── utils/                 # Utilities
│   └── public/
├── mysql/
│   └── init.sql                   # Database schema
├── docs/
│   ├── PROGRESS.md                # Project progress
│   ├── ARCHITECTURE.md            # This file
│   ├── DECISIONS.md               # Design decisions
│   ├── TODO.md                    # Task queue
│   └── AUTO-TRIGGER.md            # Auto-continue status
├── logs/
│   └── claude-[timestamp].log     # Session logs
└── CLAUDE.md                       # Maintainer instructions
```

---

## Core Modules

### 1. Authentication Service (Planned)
- Multi-provider OAuth (Google, Microsoft, GitHub)
- JWT token management
- Session handling

### 2. Aggregator Service (Planned)
- External API connectors
- Webhook handlers
- Data synchronization

### 3. AI Engine (Planned)
- NLP task parser
- Prioritization algorithm
- Daily digest generator

### 4. Notification Service (Planned)
- Email notifications
- Slack integration
- Telegram bot

### 5. Analytics Engine (Planned)
- Metrics calculation
- Report generation
- Insights extraction

---

## Database Schema

### Current Tables

#### tasks
```sql
CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    priority INT DEFAULT 1,
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### events
```sql
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    all_day BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Planned Tables

- users (authentication)
- integrations (external connections)
- habits (habit tracking)
- analytics (productivity metrics)
- notifications (notification queue)

---

## API Endpoints

### Current
- `GET /` - API status
- `GET /health` - Health check
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `GET /api/events` - List events
- `POST /api/events` - Create event

### Planned
- Authentication: `/api/auth/*`
- Integrations: `/api/integrations/*`
- Analytics: `/api/analytics/*`
- AI: `/api/ai/*`

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | React | 18.2.0 |
| Styling | Tailwind CSS | 3.2.0 |
| Backend | FastAPI | Latest |
| Database | MySQL | 8.x |
| Server | Uvicorn | Latest |
| Routing | React Router | 6.21.0 |
| HTTP Client | Axios | 1.13.1 |

---

## Deployment Considerations

### Development
- Backend: `uvicorn backend.main:app --reload`
- Frontend: `npm run dev` (Vite)

### Production
- Container: Docker
- Orchestration: Kubernetes (planned)
- Frontend: Vercel/Netlify (alternative)
- CI/CD: GitHub Actions

---

## Security Considerations

1. **CORS**: Configure proper origins
2. **Rate Limiting**: Implement per-user limits
3. **Input Validation**: Pydantic models
4. **SQL Injection**: Parameterized queries
5. **Secrets**: Environment variables only
6. **HTTPS**: Enforced in production
