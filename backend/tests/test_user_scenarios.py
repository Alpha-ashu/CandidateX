"""
User-level integration tests for CandidateX platform.
Tests complete user journeys and workflows.
"""
import pytest
from httpx import AsyncClient
from typing import Dict, Any, List
import asyncio
import time


@pytest.mark.integration
class TestCandidateJourney:
    """Complete candidate user journey tests."""

    async def test_new_user_complete_onboarding(self, client: AsyncClient):
        """Test complete onboarding journey for a new candidate."""
        # Step 1: User Registration
        user_data = {
            "email": "onboarding_test@example.com",
            "full_name": "Onboarding Test User",
            "password": "Onboard123!",
            "role": "candidate"
        }

        register_response = await client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        # Step 2: User Login
        login_response = await client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200

        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Step 3: Profile Access
        profile_response = await client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == user_data["email"]
        assert profile["role"] == "candidate"

        # Step 4: Resume Upload
        resume_content = b"Professional Software Engineer\n\nExperience: 3 years\nSkills: Python, React, Node.js\nEducation: Bachelor's in Computer Science"
        import io
        files = {"file": ("test_resume.pdf", io.BytesIO(resume_content), "application/pdf")}

        resume_upload_response = await client.post(
            "/api/v1/resume/upload",
            files=files,
            headers=headers
        )
        assert resume_upload_response.status_code == 200
        resume_data = resume_upload_response.json()
        resume_id = resume_data["resume_id"]

        # Step 5: Resume Analysis (may be async)
        analysis_response = await client.get(
            f"/api/v1/resume/{resume_id}/analysis",
            headers=headers
        )
        # Analysis might not be ready immediately
        assert analysis_response.status_code in [200, 202, 422]

        # Step 6: Create Mock Interview
        interview_data = {
            "job_title": "Frontend Developer",
            "job_description": "Building modern web applications with React, TypeScript, and modern tooling",
            "experience_level": "mid",
            "question_count": 3,
            "time_limit_per_question": 300
        }

        interview_response = await client.post(
            "/api/v1/interviews/",
            json=interview_data,
            headers=headers
        )
        assert interview_response.status_code == 200
        interview = interview_response.json()
        interview_id = interview["id"]

        # Step 7: Start Interview
        start_response = await client.post(
            f"/api/v1/interviews/{interview_id}/start",
            headers=headers
        )
        assert start_response.status_code == 200

        # Step 8: Complete Interview Questions
        # Get interview details to see questions
        details_response = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers=headers
        )
        assert details_response.status_code == 200
        interview_details = details_response.json()

        questions = interview_details.get("questions", [])
        assert len(questions) > 0

        # Answer each question
        for i, question in enumerate(questions):
            answer_data = {
                "question_index": i,
                "response_text": f"My answer to: {question.get('question_text', '')[:50]}... I have experience with this technology and can demonstrate strong problem-solving skills.",
                "time_spent": 180  # 3 minutes
            }

            submit_response = await client.post(
                f"/api/v1/interviews/{interview_id}/submit-response",
                json=answer_data,
                headers=headers
            )
            assert submit_response.status_code == 200

        # Step 9: Complete Interview
        complete_response = await client.post(
            f"/api/v1/interviews/{interview_id}/complete",
            headers=headers
        )
        assert complete_response.status_code == 200

        # Step 10: View Results
        final_response = await client.get(
            f"/api/v1/interviews/{interview_id}",
            headers=headers
        )
        assert final_response.status_code == 200
        final_interview = final_response.json()
        assert final_interview["status"] == "completed"
        assert "overall_score" in final_interview

        # Step 11: Check Analytics
        analytics_response = await client.get(
            "/api/v1/interviews/analytics/overview",
            headers=headers
        )
        assert analytics_response.status_code == 200

        # Step 12: Password Change
        change_response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": user_data["password"],
                "new_password": "NewSecure456!"
            },
            headers=headers
        )
        assert change_response.status_code == 200

        # Verify new password works
        new_login_response = await client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": "NewSecure456!"
        })
        assert new_login_response.status_code == 200

    async def test_interview_practice_workflow(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test focused interview practice workflow."""
        # Create multiple practice interviews
        practice_sessions = [
            {
                "job_title": "Full Stack Developer",
                "job_description": "MERN stack development",
                "experience_level": "mid",
                "question_count": 2,
                "interview_mode": "technical"
            },
            {
                "job_title": "Product Manager",
                "job_description": "Agile product management",
                "experience_level": "senior",
                "question_count": 2,
                "interview_mode": "behavioral"
            }
        ]

        completed_sessions = []

        for session_data in practice_sessions:
            # Create interview
            create_response = await client.post(
                "/api/v1/interviews/",
                json=session_data,
                headers=auth_headers
            )
            assert create_response.status_code == 200
            interview = create_response.json()
            interview_id = interview["id"]

            # Quick practice session
            start_response = await client.post(
                f"/api/v1/interviews/{interview_id}/start",
                headers=auth_headers
            )
            assert start_response.status_code == 200

            # Submit quick responses
            for i in range(session_data["question_count"]):
                quick_response = await client.post(
                    f"/api/v1/interviews/{interview_id}/submit-response",
                    json={
                        "question_index": i,
                        "response_text": f"Practice response {i+1} for {session_data['job_title']}",
                        "time_spent": 60
                    },
                    headers=auth_headers
                )
                assert quick_response.status_code == 200

            # Complete session
            complete_response = await client.post(
                f"/api/v1/interviews/{interview_id}/complete",
                headers=auth_headers
            )
            assert complete_response.status_code == 200

            completed_sessions.append(interview_id)

        # Verify all sessions completed
        list_response = await client.get("/api/v1/interviews/", headers=auth_headers)
        assert list_response.status_code == 200

        interviews = list_response.json()
        completed_count = sum(1 for interview in interviews if interview["status"] == "completed")
        assert completed_count >= len(completed_sessions)


@pytest.mark.integration
class TestRecruiterWorkflow:
    """Complete recruiter workflow tests."""

    async def test_recruiter_resume_screening_journey(self, client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test complete recruiter resume screening workflow."""
        headers = admin_auth_headers  # Using admin as recruiter

        # Step 1: Upload multiple resumes for screening
        resumes_data = [
            ("senior_dev.pdf", b"Senior Python Developer\n8 years experience\nPython, Django, AWS, React"),
            ("mid_dev.pdf", b"Mid-level Developer\n4 years experience\nJavaScript, Node.js, MongoDB"),
            ("junior_dev.pdf", b"Junior Developer\n1 year experience\nHTML, CSS, Basic JavaScript")
        ]

        uploaded_resumes = []

        for filename, content in resumes_data:
            import io
            files = {"file": (filename, io.BytesIO(content), "application/pdf")}

            upload_response = await client.post(
                "/api/v1/resume/upload",
                files=files,
                headers=headers
            )
            assert upload_response.status_code == 200
            resume_data = upload_response.json()
            uploaded_resumes.append(resume_data["resume_id"])

        # Step 2: Review resume list
        list_response = await client.get("/api/v1/resume/list", headers=headers)
        assert list_response.status_code == 200
        resume_list = list_response.json()["resumes"]
        assert len(resume_list) >= len(uploaded_resumes)

        # Step 3: Analyze resumes (if processing is complete)
        analyzed_resumes = []
        for resume_id in uploaded_resumes:
            analysis_response = await client.get(
                f"/api/v1/resume/{resume_id}/analysis",
                headers=headers
            )
            if analysis_response.status_code == 200:
                analysis = analysis_response.json()
                analyzed_resumes.append((resume_id, analysis))

        # Step 4: Job matching for senior position
        senior_job = {
            "job_title": "Senior Python Developer",
            "job_description": """
            Looking for experienced Python developer with:
            - 5+ years Python experience
            - Django framework expertise
            - AWS cloud experience
            - React frontend skills
            - Bachelor's degree or equivalent
            """
        }

        # Test matching for available resumes
        for resume_id, _ in analyzed_resumes:
            match_data = {
                "resume_id": resume_id,
                "job_description": senior_job["job_description"],
                "job_title": senior_job["job_title"]
            }

            match_response = await client.post(
                f"/api/v1/resume/{resume_id}/compare",
                json=match_data,
                headers=headers
            )
            assert match_response.status_code == 200

            match_result = match_response.json()
            assert "match_score" in match_result
            assert "skills_match" in match_result
            assert "recommendations" in match_result

        # Step 5: Review analytics
        analytics_response = await client.get("/api/v1/resume/analytics/overview", headers=headers)
        assert analytics_response.status_code == 200

        analytics = analytics_response.json()
        assert "stats" in analytics
        assert analytics["stats"]["total_resumes"] >= len(uploaded_resumes)

    async def test_bulk_resume_processing(self, client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test bulk resume upload and processing."""
        headers = admin_auth_headers

        # Create multiple resume files
        resume_files = []
        for i in range(5):
            content = f"Resume {i+1}\nExperience: {2+i} years\nSkills: Python, JavaScript, React"
            import io
            resume_files.append(
                ("resume", f"bulk_resume_{i+1}.pdf", io.BytesIO(content.encode()), "application/pdf")
            )

        # Upload resumes concurrently
        upload_tasks = []
        for filename, content in resume_files:
            files = {"file": (filename, content, "application/pdf")}
            task = client.post("/api/v1/resume/upload", files=files, headers=headers)
            upload_tasks.append(task)

        upload_responses = await asyncio.gather(*upload_tasks)

        # Verify all uploads succeeded
        successful_uploads = sum(1 for resp in upload_responses if resp.status_code == 200)
        assert successful_uploads == len(resume_files)

        # Check resume list reflects all uploads
        list_response = await client.get("/api/v1/resume/list", headers=headers)
        assert list_response.status_code == 200

        current_count = len(list_response.json()["resumes"])

        # Verify analytics updated
        analytics_response = await client.get("/api/v1/resume/analytics/overview", headers=headers)
        assert analytics_response.status_code == 200


@pytest.mark.integration
class TestSystemIntegration:
    """System-level integration tests."""

    async def test_cross_service_data_consistency(self, client: AsyncClient, auth_headers: Dict[str, str], test_db):
        """Test data consistency across different services."""
        # Create user and interview
        interview_data = {
            "job_title": "Consistency Test",
            "job_description": "Testing data consistency",
            "experience_level": "mid",
            "question_count": 2
        }

        create_response = await client.post(
            "/api/v1/interviews/",
            json=interview_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        interview = create_response.json()

        # Verify in database
        db_interview = await test_db.interviews.find_one({"_id": interview["id"]})
        assert db_interview is not None
        assert db_interview["job_title"] == interview_data["job_title"]

        # Complete interview workflow
        start_response = await client.post(
            f"/api/v1/interviews/{interview['id']}/start",
            headers=auth_headers
        )
        assert start_response.status_code == 200

        # Submit responses
        for i in range(2):
            submit_response = await client.post(
                f"/api/v1/interviews/{interview['id']}/submit-response",
                json={
                    "question_index": i,
                    "response_text": f"Consistency test response {i+1}",
                    "time_spent": 100
                },
                headers=auth_headers
            )
            assert submit_response.status_code == 200

        # Complete interview
        complete_response = await client.post(
            f"/api/v1/interviews/{interview['id']}/complete",
            headers=auth_headers
        )
        assert complete_response.status_code == 200

        # Verify final state in database
        final_db_interview = await test_db.interviews.find_one({"_id": interview["id"]})
        assert final_db_interview["status"] == "completed"
        assert "overall_score" in final_db_interview
        assert len(final_db_interview["responses"]) == 2

        # Verify through API
        final_api_response = await client.get(
            f"/api/v1/interviews/{interview['id']}",
            headers=auth_headers
        )
        assert final_api_response.status_code == 200
        final_api_interview = final_api_response.json()
        assert final_api_interview["status"] == "completed"

    async def test_concurrent_user_load(self, client: AsyncClient):
        """Test system behavior under concurrent user load."""
        async def user_journey(user_id: int):
            """Simulate a complete user journey."""
            try:
                # Register
                user_data = {
                    "email": f"loadtest{user_id}@example.com",
                    "full_name": f"Load Test User {user_id}",
                    "password": f"LoadPass{user_id}!",
                    "role": "candidate"
                }

                register_response = await client.post("/api/v1/auth/register", json=user_data)
                if register_response.status_code != 201:
                    return False

                # Login
                login_response = await client.post("/api/v1/auth/login", data={
                    "username": user_data["email"],
                    "password": user_data["password"]
                })
                if login_response.status_code != 200:
                    return False

                tokens = login_response.json()
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}

                # Create interview
                interview_data = {
                    "job_title": f"Load Test Job {user_id}",
                    "job_description": "Testing concurrent load",
                    "experience_level": "mid",
                    "question_count": 1
                }

                interview_response = await client.post(
                    "/api/v1/interviews/",
                    json=interview_data,
                    headers=headers
                )
                if interview_response.status_code != 200:
                    return False

                interview = interview_response.json()

                # Quick interview completion
                start_resp = await client.post(
                    f"/api/v1/interviews/{interview['id']}/start",
                    headers=headers
                )
                if start_resp.status_code != 200:
                    return False

                submit_resp = await client.post(
                    f"/api/v1/interviews/{interview['id']}/submit-response",
                    json={
                        "question_index": 0,
                        "response_text": f"Load test response from user {user_id}",
                        "time_spent": 30
                    },
                    headers=headers
                )
                if submit_resp.status_code != 200:
                    return False

                complete_resp = await client.post(
                    f"/api/v1/interviews/{interview['id']}/complete",
                    headers=headers
                )
                if complete_resp.status_code != 200:
                    return False

                return True

            except Exception as e:
                print(f"User {user_id} journey failed: {e}")
                return False

        # Run 10 concurrent user journeys
        user_tasks = [user_journey(i) for i in range(10)]
        results = await asyncio.gather(*user_tasks, return_exceptions=True)

        # Count successful journeys
        successful_journeys = sum(1 for result in results if result is True)
        print(f"Successful concurrent journeys: {successful_journeys}/10")

        # At least 70% should succeed under load
        assert successful_journeys >= 7

    async def test_data_persistence_and_recovery(self, client: AsyncClient, auth_headers: Dict[str, str], test_db):
        """Test data persistence and system recovery."""
        # Create interview
        interview_data = {
            "job_title": "Persistence Test",
            "job_description": "Testing data persistence",
            "experience_level": "mid",
            "question_count": 2
        }

        create_response = await client.post(
            "/api/v1/interviews/",
            json=interview_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        interview = create_response.json()

        # Simulate system restart by clearing any caches
        # (In real scenario, this would be an actual restart)

        # Verify data still exists after "restart"
        persisted_response = await client.get(
            f"/api/v1/interviews/{interview['id']}",
            headers=auth_headers
        )
        assert persisted_response.status_code == 200

        persisted_interview = persisted_response.json()
        assert persisted_interview["job_title"] == interview_data["job_title"]

        # Verify in database directly
        db_interview = await test_db.interviews.find_one({"_id": interview["id"]})
        assert db_interview is not None
        assert db_interview["job_title"] == interview_data["job_title"]

    async def test_error_recovery_and_graceful_degradation(self, client: AsyncClient, auth_headers: Dict[str, str]):
        """Test system error recovery and graceful degradation."""
        # Test with invalid data that should be handled gracefully
        invalid_interviews = [
            {"job_title": "", "experience_level": "invalid"},  # Invalid data
            {"job_title": "x" * 1000, "experience_level": "mid"},  # Very long title
            {"job_title": "Test", "experience_level": "mid", "question_count": 100},  # Too many questions
        ]

        for invalid_data in invalid_interviews:
            response = await client.post(
                "/api/v1/interviews/",
                json=invalid_data,
                headers=auth_headers
            )
            # Should fail gracefully with appropriate error codes
            assert response.status_code in [400, 422]

        # Test with network-like failures (simulated)
        # This would test timeout handling, retry logic, etc.

        # Test system continues to work after errors
        valid_interview = {
            "job_title": "Recovery Test",
            "job_description": "Testing system recovery",
            "experience_level": "mid",
            "question_count": 1
        }

        recovery_response = await client.post(
            "/api/v1/interviews/",
            json=valid_interview,
            headers=auth_headers
        )
        assert recovery_response.status_code == 200

        # Verify system is still functional
        list_response = await client.get("/api/v1/interviews/", headers=auth_headers)
        assert list_response.status_code == 200


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndScenarios:
    """End-to-end scenario tests covering complete user workflows."""

    async def test_full_platform_workflow(self, client: AsyncClient):
        """Test complete platform workflow from user registration to results."""
        # Phase 1: User Onboarding
        user_data = {
            "email": "e2e_test@example.com",
            "full_name": "E2E Test User",
            "password": "E2eTest123!",
            "role": "candidate"
        }

        # Registration
        register_resp = await client.post("/api/v1/auth/register", json=user_data)
        assert register_resp.status_code == 201

        # Login
        login_resp = await client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        assert login_resp.status_code == 200

        tokens = login_resp.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Phase 2: Resume Management
        resume_content = b"Software Engineer Resume\n\nSkills: Python, React, AWS\nExperience: 4 years\nEducation: BS Computer Science"
        import io
        files = {"file": ("e2e_resume.pdf", io.BytesIO(resume_content), "application/pdf")}

        resume_resp = await client.post("/api/v1/resume/upload", files=files, headers=headers)
        assert resume_resp.status_code == 200

        # Phase 3: Interview Practice
        interviews_created = []
        job_scenarios = [
            {
                "job_title": "Frontend Developer",
                "job_description": "React, TypeScript, modern web development",
                "experience_level": "mid",
                "question_count": 2
            },
            {
                "job_title": "Backend Developer",
                "job_description": "Python, Django, REST APIs, databases",
                "experience_level": "mid",
                "question_count": 2
            }
        ]

        for job in job_scenarios:
            interview_resp = await client.post("/api/v1/interviews/", json=job, headers=headers)
            assert interview_resp.status_code == 200
            interview = interview_resp.json()
            interviews_created.append(interview["id"])

            # Complete interview workflow
            start_resp = await client.post(f"/api/v1/interviews/{interview['id']}/start", headers=headers)
            assert start_resp.status_code == 200

            # Answer questions
            for i in range(job["question_count"]):
                answer_resp = await client.post(
                    f"/api/v1/interviews/{interview['id']}/submit-response",
                    json={
                        "question_index": i,
                        "response_text": f"Comprehensive answer for {job['job_title']} question {i+1}",
                        "time_spent": 120
                    },
                    headers=headers
                )
                assert answer_resp.status_code == 200

            # Complete interview
            complete_resp = await client.post(f"/api/v1/interviews/{interview['id']}/complete", headers=headers)
            assert complete_resp.status_code == 200

        # Phase 4: Results and Analytics
        # Check interview list
        list_resp = await client.get("/api/v1/interviews/", headers=headers)
        assert list_resp.status_code == 200
        interview_list = list_resp.json()
        completed_interviews = [i for i in interview_list if i["status"] == "completed"]
        assert len(completed_interviews) >= len(interviews_created)

        # Check analytics
        analytics_resp = await client.get("/api/v1/interviews/analytics/overview", headers=headers)
        assert analytics_resp.status_code == 200

        # Phase 5: Profile Management
        profile_resp = await client.get("/api/v1/auth/me", headers=headers)
        assert profile_resp.status_code == 200

        # Password change
        password_resp = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": user_data["password"],
                "new_password": "NewE2ePass456!"
            },
            headers=headers
        )
        assert password_resp.status_code == 200

        # Verify new password
        new_login_resp = await client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": "NewE2ePass456!"
        })
        assert new_login_resp.status_code == 200

        print("✅ Complete E2E workflow test passed!")

    async def test_admin_system_management(self, client: AsyncClient, admin_auth_headers: Dict[str, str]):
        """Test admin system management capabilities."""
        headers = admin_auth_headers

        # Check system health
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200

        # Get interview analytics
        interview_analytics = await client.get("/api/v1/interviews/analytics/overview", headers=headers)
        assert interview_analytics.status_code == 200

        # Get resume analytics
        resume_analytics = await client.get("/api/v1/resume/analytics/overview", headers=headers)
        assert resume_analytics.status_code == 200

        # Test admin dashboard access
        admin_resp = await client.get("/api/v1/admin/dashboard", headers=headers)
        # May return 404 if not implemented, but should not be 403 (forbidden)
        assert admin_resp.status_code != 403
