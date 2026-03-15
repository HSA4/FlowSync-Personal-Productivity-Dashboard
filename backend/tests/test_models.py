"""Model Validation Tests"""
import pytest
from datetime import datetime, date
from pydantic import ValidationError

from app.models.tasks import TaskCreate, TaskUpdate, Priority
from app.models.events import EventCreate, EventUpdate


class TestTaskModels:
    """Test task model validation"""

    def test_task_create_valid(self):
        """Test creating a valid task"""
        task = TaskCreate(
            title="Test Task",
            description="Test description",
            priority=Priority.HIGH,
            due_date=date(2025, 1, 15),
        )
        assert task.title == "Test Task"
        assert task.priority == Priority.HIGH
        assert task.due_date == date(2025, 1, 15)

    def test_task_create_minimal(self):
        """Test creating a task with minimal data"""
        task = TaskCreate(title="Test Task")
        assert task.title == "Test Task"
        assert task.completed is False
        assert task.priority == Priority.MEDIUM

    def test_task_create_invalid_title_empty(self):
        """Test validation fails for empty title"""
        with pytest.raises(ValidationError):
            TaskCreate(title="")

    def test_task_create_invalid_title_too_long(self):
        """Test validation fails for title exceeding max length"""
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * 300)

    def test_task_update_partial(self):
        """Test partial task update"""
        update = TaskUpdate(completed=True, priority=Priority.LOW)
        assert update.completed is True
        assert update.priority == Priority.LOW
        assert update.title is None

    def test_task_update_strip_whitespace(self):
        """Test whitespace stripping in updates"""
        update = TaskUpdate(title="  Test Task  ")
        assert update.title == "Test Task"

    def test_priority_enum(self):
        """Test priority enum values"""
        assert Priority.LOW == 1
        assert Priority.MEDIUM == 2
        assert Priority.HIGH == 3
        assert Priority.URGENT == 4


class TestEventModels:
    """Test event model validation"""

    def test_event_create_valid(self):
        """Test creating a valid event"""
        event = EventCreate(
            title="Test Event",
            start_time=datetime(2025, 1, 15, 10, 0),
            end_time=datetime(2025, 1, 15, 11, 0),
        )
        assert event.title == "Test Event"
        assert event.all_day is False

    def test_event_create_all_day(self):
        """Test creating an all-day event"""
        event = EventCreate(
            title="All Day Event",
            start_time=datetime(2025, 1, 15, 0, 0),
            end_time=datetime(2025, 1, 16, 0, 0),
            all_day=True,
        )
        assert event.all_day is True

    def test_event_create_invalid_end_before_start(self):
        """Test validation fails when end_time is before start_time"""
        with pytest.raises(ValidationError):
            EventCreate(
                title="Invalid Event",
                start_time=datetime(2025, 1, 15, 11, 0),
                end_time=datetime(2025, 1, 15, 10, 0),
            )

    def test_event_update_partial(self):
        """Test partial event update"""
        update = EventUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.start_time is None

    def test_event_update_invalid_end_before_start(self):
        """Test update validation fails when end_time is before start_time"""
        with pytest.raises(ValidationError):
            EventUpdate(
                start_time=datetime(2025, 1, 15, 11, 0),
                end_time=datetime(2025, 1, 15, 10, 0),
            )

    def test_event_create_without_description(self):
        """Test creating an event without description"""
        event = EventCreate(
            title="Event without description",
            start_time=datetime(2025, 1, 15, 10, 0),
            end_time=datetime(2025, 1, 15, 11, 0),
        )
        assert event.description is None
