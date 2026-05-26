"""
Integration tests for FastAPI endpoints using AAA (Arrange-Act-Assert) pattern.
"""

import pytest


class TestGetActivities:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        # Arrange: Client is ready with test data
        
        # Act: Make GET request to /activities
        response = client.get("/activities")
        
        # Assert: Verify response status and content
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_includes_participants(self, client):
        """Test that activities include participant lists"""
        # Arrange: Test activities fixture is loaded
        
        # Act: Fetch activities
        response = client.get("/activities")
        
        # Assert: Participants list is present and populated
        data = response.json()
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu"]
        assert data["Programming Class"]["participants"] == ["emma@mergington.edu"]
    
    def test_get_activities_includes_activity_details(self, client):
        """Test that activities include all required fields"""
        # Arrange: Client ready with test data
        
        # Act: Get activities
        response = client.get("/activities")
        
        # Assert: All required fields are present
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignupForActivity:
    """Test suite for POST /activities/{activity}/signup endpoint"""
    
    def test_signup_success_adds_participant(self, client):
        """Test successful signup adds participant to activity"""
        # Arrange: Fresh activities with Chess Club open
        
        # Act: Sign up new participant
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        # Assert: Success response and message
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "newstudent@mergington.edu" in response.json()["message"]
        
        # Verify participant is in the activity list
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants
        assert len(participants) == 2
    
    def test_signup_duplicate_email_rejected(self, client):
        """Test that duplicate signup is rejected"""
        # Arrange: michael@mergington.edu already signed up for Chess Club
        
        # Act: Try to sign up the same email again
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        # Assert: Request fails with 400
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_rejected(self, client):
        """Test that signup to non-existent activity is rejected"""
        # Arrange: "Nonexistent Activity" does not exist
        
        # Act: Try to sign up for non-existent activity
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        
        # Assert: Request fails with 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_at_capacity_rejected(self, client):
        """Test that signup is rejected when activity is at capacity"""
        # Arrange: Chess Club has max_participants=2, currently 1 participant
        # Add one more to reach capacity
        client.post("/activities/Chess%20Club/signup?email=second@mergington.edu")
        
        # Act: Try to sign up a third participant (exceeds capacity)
        response = client.post(
            "/activities/Chess%20Club/signup?email=third@mergington.edu"
        )
        
        # Assert: Request fails with 400 (at capacity)
        assert response.status_code == 400
        assert "capacity" in response.json()["detail"]
    
    def test_signup_multiple_activities_allowed(self, client):
        """Test that same email can sign up for different activities"""
        # Arrange: Same email will sign up for two different activities
        
        # Act: Sign up for first activity
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=student@mergington.edu"
        )
        
        # Sign up same email for second activity
        response2 = client.post(
            "/activities/Programming%20Class/signup?email=student@mergington.edu"
        )
        
        # Assert: Both signups succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities = client.get("/activities").json()
        assert "student@mergington.edu" in activities["Chess Club"]["participants"]
        assert "student@mergington.edu" in activities["Programming Class"]["participants"]


class TestRemoveParticipant:
    """Test suite for DELETE /activities/{activity}/signup/{email} endpoint"""
    
    def test_delete_participant_success(self, client):
        """Test successful removal of participant from activity"""
        # Arrange: michael@mergington.edu is signed up for Chess Club
        
        # Act: Delete the participant
        response = client.delete(
            "/activities/Chess%20Club/signup/michael%40mergington.edu"
        )
        
        # Assert: Success response
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert "michael@mergington.edu" in response.json()["message"]
        
        # Verify participant is no longer in the list
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
        assert len(participants) == 0
    
    def test_delete_nonexistent_participant_rejected(self, client):
        """Test that deletion of non-existent participant is rejected"""
        # Arrange: nobody@mergington.edu is not signed up
        
        # Act: Try to delete a participant who isn't registered
        response = client.delete(
            "/activities/Chess%20Club/signup/nobody%40mergington.edu"
        )
        
        # Assert: Request fails with 404
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]
    
    def test_delete_from_nonexistent_activity_rejected(self, client):
        """Test that deletion from non-existent activity is rejected"""
        # Arrange: "Nonexistent Activity" does not exist
        
        # Act: Try to delete from non-existent activity
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup/someone%40mergington.edu"
        )
        
        # Assert: Request fails with 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_frees_up_capacity(self, client):
        """Test that deleting a participant frees up capacity for new signups"""
        # Arrange: Fill Chess Club to capacity (max_participants=2, 1 existing)
        client.post("/activities/Chess%20Club/signup?email=second@mergington.edu")
        
        # Act: Remove one participant
        client.delete("/activities/Chess%20Club/signup/michael%40mergington.edu")
        
        # Now try to sign up a new participant
        response = client.post(
            "/activities/Chess%20Club/signup?email=third@mergington.edu"
        )
        
        # Assert: New signup succeeds
        assert response.status_code == 200
        
        # Verify new participant was added
        activities = client.get("/activities").json()
        assert "third@mergington.edu" in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 2


class TestIntegrationScenarios:
    """Integration tests for complex real-world scenarios"""
    
    def test_complete_signup_and_removal_flow(self, client):
        """Test complete flow: signup, view, remove"""
        # Arrange: Initial state with test data
        
        # Act: Sign up new participant
        signup_response = client.post(
            "/activities/Programming%20Class/signup?email=alice@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # View activities to confirm signup
        activities = client.get("/activities").json()
        assert "alice@mergington.edu" in activities["Programming Class"]["participants"]
        
        # Remove the participant
        delete_response = client.delete(
            "/activities/Programming%20Class/signup/alice%40mergington.edu"
        )
        assert delete_response.status_code == 200
        
        # Assert: Verify participant is removed
        activities = client.get("/activities").json()
        assert "alice@mergington.edu" not in activities["Programming Class"]["participants"]
    
    def test_multiple_participants_management(self, client):
        """Test managing multiple participants in single activity"""
        # Arrange: Programming Class with room for multiple signups
        
        # Act: Add multiple new participants
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        for email in emails:
            response = client.post(
                f"/activities/Programming%20Class/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Assert: All participants are registered
        activities = client.get("/activities").json()
        participants = activities["Programming Class"]["participants"]
        assert len(participants) == 4  # 1 original + 3 new
        for email in emails:
            assert email in participants
        
        # Remove one participant
        client.delete("/activities/Programming%20Class/signup/bob%40mergington.edu")
        
        # Assert: Correct participant was removed
        activities = client.get("/activities").json()
        participants = activities["Programming Class"]["participants"]
        assert "bob@mergington.edu" not in participants
        assert len(participants) == 3
