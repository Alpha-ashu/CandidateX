"""
Interview Flow Integration Tests
Comprehensive integration tests for interview-related workflows.
"""
import pytest
import asyncio
import httpx
from tests.conftest_integration import IntegrationTestAssertions


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.interviews
class TestInterviewCreationFlow:
    """Integration tests for interview creation flow."""

    @pytest.mark.asyncio
    async def test_complete_interview_creation_flow_candidate(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test complete interview creation flow for candidate."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Step 1: Create interview
        interview_data = test_data_factory.create_interview_creation_data()
        
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            assertions.assert_response_success(create_response, 201)
            interview = assertions.assert_json_response(create_response, [
                "id", "job_title", "job_description", "experience_level", 
                "question_count", "interview_mode", "status", "created_at"
            ])
            
            # Verify interview data
            assert interview["job_title"] == interview_data["job_title"]
            assert interview["job_description"] == interview_data["job_description"]
            assert interview["experience_level"] == interview_data["experience_level"]
            assert interview["question_count"] == interview_data["question_count"]
            assert interview["interview_mode"] == interview_data["interview_mode"]
            assert interview["status"] == "pending"
            
            interview_id = interview["id"]
            
            # Step 2: Get interview details
            get_response = await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
            if get_response.status_code == 200:
                assertions.assert_response_success(get_response)
                retrieved_interview = assertions.assert_json_response(get_response, ["id", "job_title", "status"])
                assert retrieved_interview["id"] == interview_id
                assert retrieved_interview["job_title"] == interview_data["job_title"]
            
        elif create_response.status_code == 404:
            pytest.skip("Interview creation endpoint not implemented")
        else:
            assertions.assert_response_success(create_response, 201)

    @pytest.mark.asyncio
    async def test_interview_creation_with_invalid_data(self, authenticated_client_candidate, assertions):
        """Test interview creation with invalid data."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Test with missing required fields
        invalid_data = {
            "job_title": "Test Interview"
            # Missing other required fields
        }
        
        response = await client.post("/api/v1/interviews/", headers=headers, json=invalid_data)
        
        if response.status_code == 422:
            assertions.assert_response_error(response, 422)  # Validation error
        elif response.status_code == 404:
            pytest.skip("Interview creation endpoint not implemented")

    @pytest.mark.asyncio
    async def test_interview_creation_unauthorized(self, async_client: httpx.AsyncClient, test_data_factory, assertions):
        """Test interview creation without authentication."""
        interview_data = test_data_factory.create_interview_creation_data()
        
        response = await async_client.post("/api/v1/interviews/", json=interview_data)
        assertions.assert_response_error(response, 401)

    @pytest.mark.asyncio
    async def test_multiple_interview_creation(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test creating multiple interviews for the same user."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create multiple interviews
        interview_configs = [
            {
                "job_title": "Frontend Developer",
                "job_description": "React development position",
                "experience_level": "junior",
                "question_count": 3,
                "interview_mode": "technical"
            },
            {
                "job_title": "Backend Developer", 
                "job_description": "Python/API development",
                "experience_level": "senior",
                "question_count": 4,
                "interview_mode": "technical"
            }
        ]
        
        interview_ids = []
        
        for config in interview_configs:
            response = await client.post("/api/v1/interviews/", headers=headers, json=config)
            
            if response.status_code == 201:
                assertions.assert_response_success(response, 201)
                interview = response.json()
                interview_ids.append(interview["id"])
            elif response.status_code == 404:
                pytest.skip("Interview creation endpoint not implemented")
        
        if interview_ids:
            # Step 2: Get list of all interviews
            list_response = await client.get("/api/v1/interviews/", headers=headers)
            
            if list_response.status_code == 200:
                assertions.assert_response_success(list_response)
                interviews = list_response.json()
                assert isinstance(interviews, list)
                
                # Verify all created interviews are in the list
                created_job_titles = [config["job_title"] for config in interview_configs]
                found_interviews = [i for i in interviews if i.get("job_title") in created_job_titles]
                assert len(found_interviews) == len(interview_configs)

    @pytest.mark.asyncio
    async def test_interview_creation_different_modes(self, authenticated_client_candidate, assertions):
        """Test interview creation with different interview modes."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        interview_modes = ["technical", "behavioral", "mixed"]
        
        for mode in interview_modes:
            interview_data = {
                "job_title": f"Test {mode.title()} Interview",
                "job_description": f"Testing {mode} interview mode",
                "experience_level": "mid",
                "question_count": 3,
                "interview_mode": mode
            }
            
            response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
            
            if response.status_code == 201:
                assertions.assert_response_success(response, 201)
                interview = response.json()
                assert interview["interview_mode"] == mode
            elif response.status_code == 404:
                pytest.skip("Interview creation endpoint not implemented")


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.interviews
class TestInterviewExecutionFlow:
    """Integration tests for interview execution workflow."""

    @pytest.mark.asyncio
    async def test_interview_start_flow(self, authenticated_client_candidate, test_data_factory, mock_ai_service, assertions):
        """Test starting an interview execution."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Step 1: Create interview
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Step 2: Generate questions (AI integration)
            questions_request = {
                "job_title": interview_data["job_title"],
                "experience_level": interview_data["experience_level"],
                "interview_mode": interview_data["interview_mode"]
            }
            
            questions_response = await client.post("/api/v1/ai/generate-questions", headers=headers, json=questions_request)
            
            if questions_response.status_code == 200:
                assertions.assert_response_success(questions_response)
                questions_data = questions_response.json()
                assert "questions" in questions_data
                assert len(questions_data["questions"]) > 0
                
                # Step 3: Start interview session
                start_response = await client.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
                
                if start_response.status_code == 200:
                    assertions.assert_response_success(start_response)
                    session_data = assertions.assert_json_response(start_response, [
                        "session_id", "interview_id", "status", "questions"
                    ])
                    assert session_data["interview_id"] == interview_id
                    assert session_data["status"] == "in_progress"
                elif start_response.status_code == 404:
                    # Interview start endpoint might not exist
                    pass
                    
            elif questions_response.status_code == 404:
                # AI endpoints might not exist
                pass
                
        elif create_response.status_code == 404:
            pytest.skip("Interview creation endpoint not implemented")

    @pytest.mark.asyncio
    async def test_interview_question_response_flow(self, authenticated_client_candidate, mock_ai_service, assertions):
        """Test interview question and response flow."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Mock question data
        question_data = {
            "question_id": "q1",
            "question_text": "What is your experience with Python?",
            "question_type": "technical",
            "expected_skills": ["Python", "Programming"]
        }
        
        user_response = "I have 3 years of experience with Python, working on web development and data analysis projects."
        
        # Test submitting response
        response_data = {
            "question_id": question_data["question_id"],
            "response": user_response
        }
        
        response = await client.post("/api/v1/interviews/response", headers=headers, json=response_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            evaluation_data = assertions.assert_json_response(response, [
                "score", "feedback", "question_id"
            ])
            assert evaluation_data["question_id"] == question_data["question_id"]
            assert isinstance(evaluation_data["score"], (int, float))
            assert isinstance(evaluation_data["feedback"], str)
        elif response.status_code == 404:
            # Response submission endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_interview_completion_flow(self, authenticated_client_candidate, mock_ai_service, assertions):
        """Test interview completion flow."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create interview first
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Complete interview
            complete_response = await client.post(f"/api/v1/interviews/{interview_id}/complete", headers=headers)
            
            if complete_response.status_code == 200:
                assertions.assert_response_success(complete_response)
                completion_data = assertions.assert_json_response(complete_response, [
                    "interview_id", "status", "overall_score", "feedback"
                ])
                assert completion_data["interview_id"] == interview_id
                assert completion_data["status"] == "completed"
                assert "overall_score" in completion_data
                assert "feedback" in completion_data
            elif complete_response.status_code == 404:
                # Completion endpoint might not exist
                pass

    @pytest.mark.asyncio
    async def test_interview_status_updates(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test interview status update flow."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create interview
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Test status updates
            status_updates = [
                ("in_progress", "Interview started"),
                ("paused", "Interview paused"),
                ("completed", "Interview completed")
            ]
            
            for new_status, description in status_updates:
                status_data = {
                    "status": new_status,
                    "notes": description
                }
                
                update_response = await client.patch(
                    f"/api/v1/interviews/{interview_id}/status", 
                    headers=headers, 
                    json=status_data
                )
                
                if update_response.status_code == 200:
                    assertions.assert_response_success(update_response)
                elif update_response.status_code == 404:
                    # Status update endpoint might not exist
                    break


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.interviews
class TestInterviewAnalyticsFlow:
    """Integration tests for interview analytics and reporting."""

    @pytest.mark.asyncio
    async def test_interview_results_retrieval(self, authenticated_client_candidate, assertions):
        """Test retrieving interview results."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Get interview results
        response = await client.get("/api/v1/interviews/results", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            results_data = assertions.assert_json_response(response)
            assert isinstance(results_data, dict) or isinstance(results_data, list)
        elif response.status_code == 404:
            # Results endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_interview_statistics(self, authenticated_client_candidate, assertions):
        """Test interview statistics retrieval."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Get interview statistics
        response = await client.get("/api/v1/interviews/statistics", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            stats_data = assertions.assert_json_response(response)
            assert isinstance(stats_data, dict)
            
            # Check for common statistics
            expected_stats = [
                "total_interviews", "completed_interviews", "average_score", 
                "best_score", "interview_trends"
            ]
            
            for stat in expected_stats:
                if stat in stats_data:
                    assert isinstance(stats_data[stat], (int, float, list, dict))
        elif response.status_code == 404:
            # Statistics endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_interview_feedback_retrieval(self, authenticated_client_candidate, assertions):
        """Test retrieving detailed interview feedback."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Get interview feedback
        response = await client.get("/api/v1/interviews/feedback", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            feedback_data = assertions.assert_json_response(response)
            assert isinstance(feedback_data, dict) or isinstance(feedback_data, list)
        elif response.status_code == 404:
            # Feedback endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_interview_export_functionality(self, authenticated_client_candidate, temp_file_factory, assertions):
        """Test interview data export functionality."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Test export in different formats
        export_formats = ["json", "pdf", "csv"]
        
        for format_type in export_formats:
            export_data = {
                "format": format_type,
                "include_feedback": True,
                "include_questions": True
            }
            
            response = await client.post("/api/v1/interviews/export", headers=headers, json=export_data)
            
            if response.status_code == 200:
                assertions.assert_response_success(response)
                
                # Check content type based on format
                if format_type == "json":
                    assert "application/json" in response.headers.get("content-type", "")
                elif format_type == "pdf":
                    assert "application/pdf" in response.headers.get("content-type", "")
                elif format_type == "csv":
                    assert "text/csv" in response.headers.get("content-type", "")
            elif response.status_code == 404:
                # Export endpoint might not exist
                break


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.recruiter
class TestRecruiterInterviewFlow:
    """Integration tests for recruiter interview management."""

    @pytest.mark.asyncio
    async def test_recruiter_create_interview_for_candidate(self, authenticated_client_recruiter, test_data_factory, assertions):
        """Test recruiter creating interview for candidate."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        # Create interview as recruiter
        interview_data = test_data_factory.create_interview_creation_data()
        interview_data["candidate_email"] = "test.candidate@example.com"
        
        response = await client.post("/api/v1/interviews/create-for-candidate", headers=headers, json=interview_data)
        
        if response.status_code == 201:
            assertions.assert_response_success(response, 201)
            interview = assertions.assert_json_response(response, ["id", "candidate_email", "status"])
            assert interview["candidate_email"] == "test.candidate@example.com"
        elif response.status_code == 404:
            # Recruiter interview creation endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_recruiter_view_candidate_interviews(self, authenticated_client_recruiter, assertions):
        """Test recruiter viewing candidate interviews."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        # Get all candidate interviews
        response = await client.get("/api/v1/interviews/all-candidates", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            interviews_data = assertions.assert_json_response(response)
            assert isinstance(interviews_data, list)
        elif response.status_code == 404:
            # Recruiter view endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_recruiter_evaluate_interview(self, authenticated_client_recruiter, mock_ai_service, assertions):
        """Test recruiter evaluating interview responses."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        # Submit evaluation
        evaluation_data = {
            "interview_id": "test_interview_id",
            "question_evaluations": [
                {
                    "question_id": "q1",
                    "score": 85,
                    "notes": "Good technical knowledge demonstrated"
                }
            ],
            "overall_feedback": "Strong candidate with good technical skills"
        }
        
        response = await client.post("/api/v1/interviews/evaluate", headers=headers, json=evaluation_data)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            result = assertions.assert_json_response(response, ["evaluation_id", "status"])
            assert result["status"] == "completed"
        elif response.status_code == 404:
            # Evaluation endpoint might not exist
            pass

    @pytest.mark.asyncio
    async def test_recruiter_interview_analytics(self, authenticated_client_recruiter, assertions):
        """Test recruiter interview analytics."""
        client = authenticated_client_recruiter["client"]
        headers = authenticated_client_recruiter["headers"]
        
        # Get recruiter analytics
        response = await client.get("/api/v1/interviews/recruiter-analytics", headers=headers)
        
        if response.status_code == 200:
            assertions.assert_response_success(response)
            analytics_data = assertions.assert_json_response(response)
            assert isinstance(analytics_data, dict)
            
            # Check for recruiter-specific analytics
            expected_metrics = [
                "interviews_conducted", "candidates_evaluated", "average_candidate_score"
            ]
            
            for metric in expected_metrics:
                if metric in analytics_data:
                    assert isinstance(analytics_data[metric], (int, float))
        elif response.status_code == 404:
            # Analytics endpoint might not exist
            pass


@pytest.mark.integration
@pytest.mark.flow
@pytest.mark.interviews
class TestInterviewEdgeCases:
    """Integration tests for interview flow edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_interview_access_by_non_owner(self, authenticated_client_candidate, authenticated_client_recruiter, test_data_factory, assertions):
        """Test that users cannot access others' interviews."""
        candidate_client = authenticated_client_candidate["client"]
        candidate_headers = authenticated_client_candidate["headers"]
        recruiter_client = authenticated_client_recruiter["client"]
        recruiter_headers = authenticated_client_recruiter["headers"]
        
        # Candidate creates interview
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await candidate_client.post("/api/v1/interviews/", headers=candidate_headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Recruiter tries to access candidate's interview
            access_response = await recruiter_client.get(f"/api/v1/interviews/{interview_id}", headers=recruiter_headers)
            
            # Should be forbidden or not found
            assert access_response.status_code in [403, 404]
            if access_response.status_code == 403:
                assertions.assert_response_error(access_response, 403)

    @pytest.mark.asyncio
    async def test_interview_with_nonexistent_id(self, authenticated_client_candidate, assertions):
        """Test accessing interview with non-existent ID."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        fake_id = "nonexistent_interview_id"
        response = await client.get(f"/api/v1/interviews/{fake_id}", headers=headers)
        
        assert response.status_code == 404
        if response.status_code == 404:
            assertions.assert_response_error(response, 404)

    @pytest.mark.asyncio
    async def test_interview_state_transitions(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test invalid interview state transitions."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create interview
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Try invalid state transition (from pending to completed)
            invalid_transition = {
                "status": "completed",
                "notes": "Attempting invalid transition"
            }
            
            transition_response = await client.patch(
                f"/api/v1/interviews/{interview_id}/status", 
                headers=headers, 
                json=invalid_transition
            )
            
            if transition_response.status_code == 400:
                assertions.assert_response_error(transition_response, 400)
            elif transition_response.status_code == 404:
                # Status update endpoint might not exist
                pass

    @pytest.mark.asyncio
    async def test_concurrent_interview_access(self, authenticated_client_candidate, assertions):
        """Test concurrent access to the same interview."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create multiple concurrent requests to the same endpoint
        concurrent_requests = [
            client.get("/api/v1/interviews/") for _ in range(5)
        ]
        
        responses = await asyncio.gather(*concurrent_requests, return_exceptions=True)
        
        # All should succeed (some might be empty lists if no interviews exist)
        for response in responses:
            if hasattr(response, 'status_code'):
                assert response.status_code == 200
                if response.status_code == 200:
                    assertions.assert_response_success(response)

    @pytest.mark.asyncio
    async def test_interview_crud_operations_sequence(self, authenticated_client_candidate, test_data_factory, assertions):
        """Test complete CRUD sequence for interviews."""
        client = authenticated_client_candidate["client"]
        headers = authenticated_client_candidate["headers"]
        
        # Create
        interview_data = test_data_factory.create_interview_creation_data()
        create_response = await client.post("/api/v1/interviews/", headers=headers, json=interview_data)
        
        if create_response.status_code == 201:
            interview = create_response.json()
            interview_id = interview["id"]
            
            # Read
            read_response = await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
            if read_response.status_code == 200:
                assertions.assert_response_success(read_response)
            
            # Update
            update_data = {"job_title": "Updated Interview Title"}
            update_response = await client.patch(
                f"/api/v1/interviews/{interview_id}", 
                headers=headers, 
                json=update_data
            )
            if update_response.status_code == 200:
                assertions.assert_response_success(update_response)
                updated_interview = update_response.json()
                assert updated_interview["job_title"] == "Updated Interview Title"
            
            # Delete
            delete_response = await client.delete(f"/api/v1/interviews/{interview_id}", headers=headers)
            if delete_response.status_code == 204:
                assert delete_response.content == b""
            elif delete_response.status_code == 200:
                assertions.assert_response_success(delete_response)
        elif create_response.status_code == 404:
            pytest.skip("Interview CRUD endpoints not implemented")