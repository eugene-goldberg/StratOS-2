import os
import sys
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app
from routers import analysis
from models.user import UserResponse
from dependencies import get_current_active_user, get_current_user_id

client = TestClient(app)

user = UserResponse(
    id=uuid.uuid4(),
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
        assert uid == str(user.id)
        return [{"linkage_id": "1"}]

    monkeypatch.setattr(analysis.analysis_service, "discover_so_linkages", mock_discover)
    response = client.post("/api/analysis/so-linkage/discover", params={"topic_context": "growth"})
    assert response.status_code == 200
    assert response.json() == [{"linkage_id": "1"}]
