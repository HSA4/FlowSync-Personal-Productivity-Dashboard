# FlowSync - Personal Productivity Dashboard

A unified productivity dashboard that integrates with your favorite tools (Todoist, Google Calendar, Gmail, etc.) to provide a single view of your tasks, events, and insights.

## Features

- **Unified Dashboard**: View tasks and calendar events in one place
- **External Integrations**: Connect Todoist, Google Calendar, and more
- **Real-time Sync**: Automatic synchronization with external services
- **OAuth Authentication**: Secure Google OAuth integration
- **Modern UI**: Clean, responsive React + Vite frontend
- **FastAPI Backend**: High-performance Python backend with PostgreSQL

## Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS
- React Router
- Axios

### Backend
- FastAPI
- PostgreSQL
- Pydantic
- psycopg2
- Python JWT for authentication

### DevOps
- Docker & Docker Compose
- GitHub Actions for CI/CD

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/FlowSync-Personal-Productivity-Dashboard.git
cd FlowSync-Personal-Productivity-Dashboard
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start all services:
```bash
docker-compose up -d
```

4. The application will be available at:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Backend

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```bash
# Using Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine

# Run migrations
psql -h localhost -U postgres -d flowsync -f mysql/schema.sql
psql -h localhost -U postgres -d flowsync -f backend/migrations/001_create_users_table.sql
psql -h localhost -U postgres -d flowsync -f backend/migrations/002_create_integrations_table.sql
```

3. Configure environment:
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_DATABASE=flowsync
```

4. Run the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open http://localhost:5173

## Environment Variables

### Backend (.env)
```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=flowsync

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OAuth (Google)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/callback

# Integrations
TODOIST_CLIENT_ID=your-todoist-client-id
TODOIST_CLIENT_SECRET=your-todoist-client-secret

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
```

## Database Schema

```
users
├── id (SERIAL PRIMARY KEY)
├── email (VARCHAR UNIQUE)
├── name (VARCHAR)
├── avatar_url (VARCHAR)
├── provider (ENUM: google, microsoft, github, email)
├── provider_id (VARCHAR)
├── is_active (BOOLEAN)
├── refresh_token (TEXT)
└── created_at, updated_at, last_login (TIMESTAMP)

tasks
├── id (SERIAL PRIMARY KEY)
├── user_id (INTEGER)
├── title (VARCHAR)
├── description (TEXT)
├── status (VARCHAR)
├── priority (INTEGER)
├── due_date (TIMESTAMP)
├── external_id (VARCHAR)
├── external_provider (VARCHAR)
└── created_at, updated_at (TIMESTAMP)

events
├── id (SERIAL PRIMARY KEY)
├── user_id (INTEGER)
├── title (VARCHAR)
├── description (TEXT)
├── start_time (TIMESTAMP)
├── end_time (TIMESTAMP)
├── all_day (BOOLEAN)
├── external_id (VARCHAR)
├── external_provider (VARCHAR)
└── created_at, updated_at (TIMESTAMP)

integrations
├── id (SERIAL PRIMARY KEY)
├── user_id (INTEGER)
├── name (VARCHAR)
├── provider (VARCHAR)
├── access_token (TEXT)
├── refresh_token (TEXT)
├── enabled (BOOLEAN)
├── settings (JSONB)
├── last_sync (TIMESTAMP)
└── created_at, updated_at (TIMESTAMP)

sync_logs
├── id (SERIAL PRIMARY KEY)
├── integration_id (INTEGER)
├── status (ENUM: pending, in_progress, success, error)
├── items_synced (INTEGER)
├── error_message (TEXT)
├── started_at (TIMESTAMP)
└── completed_at (TIMESTAMP)
```

## API Endpoints

### Authentication
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/oauth/google` - Get Google OAuth URL
- `POST /api/v1/auth/oauth/google/callback` - Handle OAuth callback
- `POST /api/v1/auth/logout` - Logout user

### Tasks
- `GET /api/v1/tasks` - List tasks (with filtering)
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `PATCH /api/v1/tasks/{id}/toggle` - Toggle completion

### Events
- `GET /api/v1/events` - List events (with date filtering)
- `POST /api/v1/events` - Create event
- `GET /api/v1/events/{id}` - Get event
- `PUT /api/v1/events/{id}` - Update event
- `DELETE /api/v1/events/{id}` - Delete event

### Integrations
- `GET /api/v1/integrations/providers/available` - List available providers
- `GET /api/v1/integrations` - List user's integrations
- `POST /api/v1/integrations` - Create integration
- `GET /api/v1/integrations/{id}` - Get integration
- `PATCH /api/v1/integrations/{id}` - Update integration
- `DELETE /api/v1/integrations/{id}` - Delete integration
- `POST /api/v1/integrations/{id}/sync` - Trigger sync
- `GET /api/v1/integrations/oauth/{provider}` - Get OAuth URL
- `POST /api/v1/integrations/oauth/{provider}/callback` - Handle OAuth callback

## Project Structure

```
FlowSync-Personal-Productivity-Dashboard/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, security, logging
│   │   ├── db/           # Database connection
│   │   ├── models/       # Pydantic models
│   │   └── services/     # Business logic
│   ├── migrations/       # Database migrations
│   └── tests/           # API tests
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── contexts/     # React contexts
│   │   ├── hooks/        # Custom hooks
│   │   ├── pages/        # Page components
│   │   └── services/     # API service
│   └── public/
├── docs/                 # Project documentation
├── .github/             # GitHub Actions
└── docker-compose.yml   # Docker configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Roadmap

- [ ] Gmail integration for email summaries
- [ ] GitHub issues integration
- [ ] AI-powered task prioritization
- [ ] Natural language task parsing
- [ ] Mobile app (React Native)
- [ ] Browser extension
- [ ] Advanced analytics and reporting
- [ ] Team collaboration features
