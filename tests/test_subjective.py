import os
import sys
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app
from routers import subjective_input
from services.subjective_input_service import SubjectiveInputService
from models.subjective_input import LogEntry, LogEntryCreate, LogEntryType
from models.user import UserResponse
from dependencies import get_current_active_user, get_current_user_id

client = TestClient(app)

test_user = UserResponse(
    id=uuid.uuid4(),
    email="user@example.com",
    full_name="User",
    company_name="TestCo",
    job_title="CEO",
    is_active=True,
    created_at=datetime.now()
)

app.dependency_overrides[get_current_active_user] = lambda: test_user
app.dependency_overrides[get_current_user_id] = lambda: test_user.id


def test_create_log_entry(monkeypatch):
    async def mock_create(entry_data: LogEntryCreate, user_id: uuid.UUID):
        assert user_id == test_user.id
        return LogEntry(content=entry_data.content, user_id=user_id)

    monkeypatch.setattr(subjective_input.input_service, "create_log_entry", mock_create)
    monkeypatch.setattr(subjective_input, "process_log_entry_with_ai", lambda eid: None)

    response = client.post("/api/subjective/log", json={"content": "hello"})
    assert response.status_code == 201
    assert response.json()["content"] == "hello"
