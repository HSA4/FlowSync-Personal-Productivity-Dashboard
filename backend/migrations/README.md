# Database Migrations

This directory contains SQL migration scripts for the FlowSync database.

## How to Run Migrations

### Option 1: Direct MySQL Execution
```bash
mysql -h localhost -u root -p flowsync < migrations/001_create_users_table.sql
```

### Option 2: Using Docker Compose
```bash
docker-compose exec db mysql -u root -proot flowsync < migrations/001_create_users_table.sql
```

### Option 3: Using MySQL Client
```bash
mysql -h localhost -u root -p
USE flowsync;
SOURCE migrations/001_create_users_table.sql;
```

## Migration Files

| File | Description |
|------|-------------|
| 001_create_users_table.sql | Create users table for authentication |
| 002_add_sessions_table.sql | (Future) Add sessions table for session management |

## Rollback

To rollback a migration, manually reverse the changes or create a rollback script.
