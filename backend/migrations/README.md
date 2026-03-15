# Database Migrations (PostgreSQL)

This directory contains SQL migration scripts for the FlowSync PostgreSQL database.

## Prerequisites

1. Ensure PostgreSQL is installed and running
2. Create the database:
   ```bash
   createdb flowsync
   # or
   psql -U postgres -c "CREATE DATABASE flowsync;"
   ```

## How to Run Migrations

### Option 1: Direct PostgreSQL Execution
```bash
psql -U postgres -d flowsync -f migrations/001_create_users_table.sql
psql -U postgres -d flowsync -f migrations/002_create_integrations_table.sql
```

### Option 2: Using Docker Compose
```bash
docker-compose exec postgres psql -U postgres -d flowsync -f /migrations/001_create_users_table.sql
docker-compose exec postgres psql -U postgres -d flowsync -f /migrations/002_create_integrations_table.sql
```

### Option 3: Using psql Client
```bash
psql -U postgres -d flowsync
\i migrations/001_create_users_table.sql
\i migrations/002_create_integrations_table.sql
```

### Option 4: Run All Migrations at Once
```bash
for migration in migrations/*.sql; do
    echo "Running $migration..."
    psql -U postgres -d flowsync -f "$migration"
done
```

## Migration Files

| File | Description |
|------|-------------|
| 001_create_users_table.sql | Create users table, add user_id to tasks/events |
| 002_create_integrations_table.sql | Create integrations and sync_logs tables |
| ../mysql/schema.sql | Initial schema with tasks/events tables |

## Database Schema Overview

### Tables
- **users**: User accounts and authentication
- **tasks**: Task management with external sync support
- **events**: Calendar events with external sync support
- **integrations**: External service connections (Todoist, Google Calendar, etc.)
- **sync_logs**: Integration synchronization history

### Key Features
- Auto-updating `updated_at` timestamps via triggers
- Foreign key constraints with CASCADE delete
- JSONB support for flexible settings storage
- Enum types for status fields
- Proper indexing for performance

## PostgreSQL Notes

- Uses `SERIAL` for auto-incrementing primary keys
- Uses `JSONB` for JSON data (better performance than JSON)
- Uses triggers for `updated_at` timestamps (no ON UPDATE)
- Uses custom ENUM types for status fields
- Uses `TIMESTAMP` instead of `DATETIME`

## Rollback

To rollback a migration, manually reverse the changes:
```bash
psql -U postgres -d flowsync -c "DROP TABLE IF EXISTS sync_logs CASCADE;"
psql -U postgres -d flowsync -c "DROP TABLE IF EXISTS integrations CASCADE;"
psql -U postgres -d flowsync -c "DROP TABLE IF EXISTS users CASCADE;"
```
