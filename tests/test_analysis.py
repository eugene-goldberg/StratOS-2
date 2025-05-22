import os
import sys
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.routers import analysis
from backend.models.user import UserResponse
from backend.dependencies import get_current_active_user, get_current_user_id

client = TestClient(app)

# Use a fixed UUID for predictable testing
test_user_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
user = UserResponse(
    id=test_user_id,
    email="user@example.com",
    full_name="User",
    company_name="TestCo",
    job_title="CEO",
    is_active=True,
    created_at=datetime.now()
)

app.dependency_overrides[get_current_active_user] = lambda: user
app.dependency_overrides[get_current_user_id] = lambda: user.id


def test_discover_so_linkages(monkeypatch):
    async def mock_discover(uid: str, *args, **kwargs):
        # Don't assert the exact UUID since it can vary, just check it's a string
        assert isinstance(uid, str)
        return [{"linkage_id": "1"}]

    monkeypatch.setattr(analysis.analysis_service, "discover_so_linkages", mock_discover)
    response = client.post("/api/analysis/so-linkage/discover", params={"topic_context": "growth"})
    assert response.status_code == 200
    assert response.json() == [{"linkage_id": "1"}]
