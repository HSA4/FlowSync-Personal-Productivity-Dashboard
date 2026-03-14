from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FlowSync API", description="Personal Productivity Dashboard API")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'flowsync')
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
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
    if connection and connection.is_connected():
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
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        tasks = cursor.fetchall()
        return tasks
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.post("/api/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO tasks (title, description, completed, priority, due_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (task.title, task.description, task.completed, task.priority, task.due_date)
        cursor.execute(query, values)
        connection.commit()
        task_id = cursor.lastrowid
        return {**task.dict(), "id": task_id}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Event endpoints
@app.get("/api/events", response_model=List[Event])
async def get_events():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM events ORDER BY start_time")
        events = cursor.fetchall()
        return events
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.post("/api/events", response_model=Event)
async def create_event(event: EventCreate):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO events (title, description, start_time, end_time, all_day)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (event.title, event.description, event.start_time, event.end_time, event.all_day)
        cursor.execute(query, values)
        connection.commit()
        event_id = cursor.lastrowid
        return {**event.dict(), "id": event_id}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)