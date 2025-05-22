import os
import sys
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.routers.planning import planning_service
from backend.models.user import UserResponse
from backend.dependencies import get_current_active_user, get_current_user_id

# Test user for dependency override
test_user = UserResponse(
    id=uuid.uuid4(),
    email="user@example.com",
    full_name="User",
    company_name="TestCo",
    job_title="CEO",
    is_active=True,
    created_at=datetime.now()
)

@pytest.fixture
def client():
    """Create test client with dependency overrides."""
    # Override authentication dependencies
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_current_user_id] = lambda: test_user.id
    
    test_client = TestClient(app)
    
    yield test_client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


def test_analyze_alignment_valid(client, monkeypatch):
    plan_id = uuid.uuid4()

    async def mock_analyze(pid: uuid.UUID, user_id: uuid.UUID):
        assert pid == plan_id
        return {"alignment": "ok"}

    monkeypatch.setattr(planning_service, "analyze_plan_alignment", mock_analyze)

    response = client.post(f"/api/planning/plans/{plan_id}/analyze-alignment")
    assert response.status_code == 200
    assert response.json() == {"alignment": "ok"}


def test_analyze_alignment_invalid_uuid(client):
    response = client.post("/api/planning/plans/not-a-uuid/analyze-alignment")
    assert response.status_code == 422

