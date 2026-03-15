# FlowSync API - Legacy Entry Point
# This file is kept for backward compatibility but the app has moved to app/main.py
# Please use: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FlowSync API", description="Personal Productivity Dashboard API")

# Database configuration (PostgreSQL)
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DATABASE', 'flowsync')
}

def get_db_connection():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# Pydantic models
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: int = 1  # 1=low, 2=medium, 3=high
    due_date: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    all_day: bool = False

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int

# API Endpoints
@app.get("/")
async def root():
    return {"message": "FlowSync API is running"}

@app.get("/health")
async def health_check():
    connection = get_db_connection()
    if connection:
        connection.close()
        return {"status": "healthy", "database": "connected"}
    else:
        return {"status": "unhealthy", "database": "disconnected"}

# Task endpoints
@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        tasks = cursor.fetchall()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.post("/api/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        query = """
        INSERT INTO tasks (title, description, completed, priority, due_date)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """
        values = (task.title, task.description, task.completed, task.priority, task.due_date)
        cursor.execute(query, values)
        connection.commit()
        result = cursor.fetchone()
        return result
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()

# Event endpoints
@app.get("/api/events", response_model=List[Event])
async def get_events():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM events ORDER BY start_time")
        events = cursor.fetchall()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.post("/api/events", response_model=Event)
async def create_event(event: EventCreate):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        query = """
        INSERT INTO events (title, description, start_time, end_time, all_day)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """
        values = (event.title, event.description, event.start_time, event.end_time, event.all_day)
        cursor.execute(query, values)
        connection.commit()
        result = cursor.fetchone()
        return result
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)