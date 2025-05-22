import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.routers.planning import planning_service

client = TestClient(app)


def test_analyze_alignment_valid(monkeypatch):
    plan_id = uuid.uuid4()

    async def mock_analyze(pid: uuid.UUID):
        assert pid == plan_id
        return {"alignment": "ok"}

    monkeypatch.setattr(planning_service, "analyze_plan_alignment", mock_analyze)

    response = client.post(f"/api/planning/plans/{plan_id}/analyze-alignment")
    assert response.status_code == 200
    assert response.json() == {"alignment": "ok"}


def test_analyze_alignment_invalid_uuid():
    response = client.post("/api/planning/plans/not-a-uuid/analyze-alignment")
    assert response.status_code == 422

