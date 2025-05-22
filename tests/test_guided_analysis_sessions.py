"""
Tests for Guided Analysis Sessions API (A1)
Testing session management endpoints for interactive SWOT/TOWS
"""

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.user import UserResponse
from backend.models.analysis import (
    AnalysisSessionCreate,
    AnalysisSessionUpdate,
    AnalysisSessionType,
    AnalysisSessionStatus,
    GuidanceRequest
)
from backend.dependencies import get_current_active_user, get_current_user_id


@pytest.fixture
def test_client():
    """Create test client for API testing with auth override"""
    test_user_id = uuid4()
    user = UserResponse(
        id=test_user_id,
        email="test@example.com",
        full_name="Test User",
        company_name="TestCo",
        job_title="CEO",
        is_active=True,
        created_at=datetime.now()
    )
    
    # Store original overrides to restore later
    original_overrides = app.dependency_overrides.copy()
    
    # Override dependencies for testing
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_current_user_id] = lambda: user.id
    
    yield TestClient(app)
    
    # Restore original overrides instead of clearing all
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture
def sample_session_data():
    """Sample data for creating analysis session"""
    return {
        "session_type": "guided_swot",
        "title": "Company Strategic Analysis",
        "description": "Q1 2024 strategic SWOT analysis",
        "topic": "market expansion",
        "company_name": "TestCo"
    }


class TestGuidedAnalysisSessions:
    """Test guided analysis session management"""
    
    def test_create_analysis_session_success(self, test_client, sample_session_data):
        """Test successful session creation"""
        response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == sample_session_data["title"]
        assert data["session_type"] == sample_session_data["session_type"]
        assert data["topic"] == sample_session_data["topic"]
        assert data["status"] == "active"
        assert "id" in data
        assert "user_id" in data
        assert "current_step" in data
        assert "step_states" in data
    
    def test_create_session_missing_required_fields(self, test_client):
        """Test session creation with missing required fields"""
        incomplete_data = {
            "title": "Test Session"
            # Missing session_type and topic
        }
        
        response = test_client.post("/api/analysis/sessions", json=incomplete_data)
        assert response.status_code == 422
    
    def test_get_analysis_session_success(self, test_client, sample_session_data):
        """Test successful session retrieval"""
        # Create session first
        create_response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        assert create_response.status_code == 201
        session_id = create_response.json()["id"]
        
        # Get session
        get_response = test_client.get(f"/api/analysis/sessions/{session_id}")
        assert get_response.status_code == 200
        
        session_data = get_response.json()
        assert session_data["id"] == session_id
        assert session_data["title"] == sample_session_data["title"]
    
    def test_get_nonexistent_session(self, test_client):
        """Test getting session that doesn't exist"""
        nonexistent_id = str(uuid4())
        response = test_client.get(f"/api/analysis/sessions/{nonexistent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_analysis_sessions_empty(self, test_client):
        """Test listing sessions when none exist"""
        response = test_client.get("/api/analysis/sessions")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_analysis_sessions_with_data(self, test_client, sample_session_data):
        """Test listing sessions with existing data"""
        # Create multiple sessions
        for i in range(3):
            session_data = sample_session_data.copy()
            session_data["title"] = f"Session {i}"
            response = test_client.post("/api/analysis/sessions", json=session_data)
            assert response.status_code == 201
        
        # List sessions
        response = test_client.get("/api/analysis/sessions")
        assert response.status_code == 200
        
        sessions = response.json()
        assert len(sessions) == 3
        assert all("id" in session for session in sessions)
    
    def test_update_analysis_session(self, test_client, sample_session_data):
        """Test updating session status and details"""
        # Create session
        create_response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Update session
        update_data = {
            "status": "paused",
            "title": "Updated Session Title"
        }
        
        response = test_client.put(f"/api/analysis/sessions/{session_id}", json=update_data)
        assert response.status_code == 200
        
        updated_session = response.json()
        assert updated_session["status"] == "paused"
        assert updated_session["title"] == "Updated Session Title"
    
    def test_delete_analysis_session(self, test_client, sample_session_data):
        """Test deleting analysis session"""
        # Create session
        create_response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Delete session
        response = test_client.delete(f"/api/analysis/sessions/{session_id}")
        assert response.status_code == 204
        
        # Verify session is gone
        get_response = test_client.get(f"/api/analysis/sessions/{session_id}")
        assert get_response.status_code == 404
    
    def test_request_session_guidance(self, test_client, sample_session_data):
        """Test requesting AI guidance for session step"""
        # Create session
        create_response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Request guidance
        guidance_data = {
            "session_id": session_id,
            "step_id": "swot_strengths",
            "context": {"additional_info": "focus on technical capabilities"}
        }
        
        response = test_client.post(f"/api/analysis/sessions/{session_id}/guidance", json=guidance_data)
        assert response.status_code == 200
        
        guidance = response.json()
        assert guidance["session_id"] == session_id
        assert guidance["step_id"] == "swot_strengths"
        assert "guiding_questions" in guidance
        assert "suggestions" in guidance
    
    def test_complete_session_step(self, test_client, sample_session_data):
        """Test marking session step as completed"""
        # Create session
        create_response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Complete step
        response = test_client.post(f"/api/analysis/sessions/{session_id}/steps/swot_strengths/complete")
        assert response.status_code == 200
        
        updated_session = response.json()
        assert "swot_strengths" in updated_session["completed_steps"]
        # Should advance to next step
        assert updated_session["current_step"] == "swot_weaknesses"
    
    def test_pause_and_resume_session(self, test_client, sample_session_data):
        """Test pausing and resuming analysis session"""
        # Create session
        create_response = test_client.post("/api/analysis/sessions", json=sample_session_data)
        session_id = create_response.json()["id"]
        
        # Pause session
        pause_response = test_client.post(f"/api/analysis/sessions/{session_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "paused"
        
        # Resume session
        resume_response = test_client.post(f"/api/analysis/sessions/{session_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "active"


class TestSessionFiltering:
    """Test session filtering and pagination"""
    
    def test_filter_sessions_by_status(self, test_client, sample_session_data):
        """Test filtering sessions by status"""
        # Create active session
        active_data = sample_session_data.copy()
        active_data["title"] = "Active Session"
        test_client.post("/api/analysis/sessions", json=active_data)
        
        # Create and pause another session
        paused_data = sample_session_data.copy()
        paused_data["title"] = "Paused Session"
        create_response = test_client.post("/api/analysis/sessions", json=paused_data)
        session_id = create_response.json()["id"]
        test_client.post(f"/api/analysis/sessions/{session_id}/pause")
        
        # Filter by active status
        response = test_client.get("/api/analysis/sessions?status_filter=active")
        assert response.status_code == 200
        
        sessions = response.json()
        assert len(sessions) == 1
        assert sessions[0]["title"] == "Active Session"
    
    def test_filter_sessions_by_type(self, test_client):
        """Test filtering sessions by session type"""
        # Create SWOT session
        swot_data = {
            "session_type": "guided_swot",
            "title": "SWOT Session",
            "topic": "analysis"
        }
        test_client.post("/api/analysis/sessions", json=swot_data)
        
        # Create TOWS session
        tows_data = {
            "session_type": "guided_tows",
            "title": "TOWS Session", 
            "topic": "strategy"
        }
        test_client.post("/api/analysis/sessions", json=tows_data)
        
        # Filter by SWOT type
        response = test_client.get("/api/analysis/sessions?session_type=guided_swot")
        assert response.status_code == 200
        
        sessions = response.json()
        assert len(sessions) == 1
        assert sessions[0]["session_type"] == "guided_swot"
    
    def test_session_pagination(self, test_client, sample_session_data):
        """Test session list pagination"""
        # Create 5 sessions
        for i in range(5):
            session_data = sample_session_data.copy()
            session_data["title"] = f"Session {i}"
            test_client.post("/api/analysis/sessions", json=session_data)
        
        # Get first page (limit 3)
        response = test_client.get("/api/analysis/sessions?limit=3&offset=0")
        assert response.status_code == 200
        
        page1 = response.json()
        assert len(page1) == 3
        
        # Get second page
        response = test_client.get("/api/analysis/sessions?limit=3&offset=3")
        assert response.status_code == 200
        
        page2 = response.json()
        assert len(page2) == 2