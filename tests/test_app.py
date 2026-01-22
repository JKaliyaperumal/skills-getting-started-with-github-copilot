"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test"""
    # Save original state
    original_activities = {
        key: {**value, "participants": value["participants"].copy()}
        for key, value in activities.items()
    }
    
    yield
    
    # Restore original state
    for key in activities:
        activities[key]["participants"] = original_activities[key]["participants"].copy()


class TestGetActivities:
    """Tests for getting activities"""
    
    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert data["Basketball"]["description"] == "Team sport focusing on basketball skills and competition"


class TestSignup:
    """Tests for signing up for activities"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        
        # Verify the participant was added
        activities_data = client.get("/activities").json()
        assert "newemail@mergington.edu" in activities_data["Basketball"]["participants"]
    
    def test_signup_duplicate(self, client, reset_activities):
        """Test signup fails if student is already signed up"""
        # Try to sign up someone already in the activity
        response = client.post(
            "/activities/Basketball/signup?email=james@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/NonexistentClub/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregister:
    """Tests for unregistering from activities"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Basketball/unregister?email=james@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify the participant was removed
        activities_data = client.get("/activities").json()
        assert "james@mergington.edu" not in activities_data["Basketball"]["participants"]
    
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregister fails if student is not signed up"""
        response = client.delete(
            "/activities/Basketball/unregister?email=notexist@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/NonexistentClub/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestIntegration:
    """Integration tests for signup and unregister flows"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up and then unregistering"""
        email = "integration@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_data = client.get("/activities").json()
        assert email in activities_data["Tennis Club"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/Tennis Club/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_data = client.get("/activities").json()
        assert email not in activities_data["Tennis Club"]["participants"]
