from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from apps.base.models import CustomUser
from apps.director.models import Meeting, Question


class TestMeetingCreation:
    """Test the critical meeting creation flow"""

    @pytest.mark.django_db
    def test_successful_meeting_with_questions_creation(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test complete meeting creation flow"""
        client.force_login(authenticated_user)

        meeting_data = {
            "title": "Test Meeting",
            "description": "Test Description",
            "duration": 30,
            # Formset management data
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "20",
            # Questions
            "form-0-description": "First question?",
            "form-1-description": "Second question?",
        }

        response = client.post(reverse("create-meeting"), data=meeting_data)

        # Should redirect to host meeting page
        assert response.status_code == 302

        # Meeting should be created
        meeting = Meeting.objects.get(title="Test Meeting")
        assert meeting.director == authenticated_user
        assert meeting.duration == 30
        assert len(meeting.access_code) == 8
        assert meeting.access_code.isdigit()

        # Questions should be created with correct positions
        questions = Question.objects.filter(meeting=meeting).order_by("position")
        assert questions.count() == 2
        assert questions[0].description == "First question?"
        assert questions[0].position == 1
        assert questions[1].description == "Second question?"
        assert questions[1].position == 2

    @pytest.mark.django_db(transaction=True)
    def test_meeting_creation_with_access_code_collision(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test handling of access code collisions"""
        client.force_login(authenticated_user)

        # Create a meeting with a specific access code
        existing_meeting = Meeting.objects.create(  # noqa: F841
            director=authenticated_user,
            title="Existing Meeting",
            description="Existing",
            duration=30,
            access_code="12345678",
        )

        # Mock generate_access_code to return the same code
        with patch("apps.director.views.generate_access_code") as mock_gen:
            mock_gen.return_value = "12345678"  # Force collision

            meeting_data = {
                "title": "New Meeting",
                "description": "New Description",
                "duration": 25,
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "1",
                "form-MAX_NUM_FORMS": "20",
                "form-0-description": "Test question?",
            }

            response = client.post(reverse("create-meeting"), data=meeting_data)

            assert response.status_code in [302, 400]

            # Verify no duplicate meeting was created
            meetings_with_title = Meeting.objects.filter(title="New Meeting")
            assert meetings_with_title.count() == 0

            # Original meeting should still exist
            assert Meeting.objects.filter(access_code="12345678").count() == 1

    @pytest.mark.django_db
    def test_invalid_form_data_handling(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test form validation errors are handled properly"""
        client.force_login(authenticated_user)

        # Missing required fields
        invalid_data = {
            "title": "",  # Empty title
            "description": "Valid description",
            "duration": 0,  # Invalid duration
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "20",
            "form-0-description": "",  # Empty question
        }

        response = client.post(reverse("create-meeting"), data=invalid_data)

        # Should stay on create page with errors
        assert response.status_code == 200
        assert "meeting_form" in response.context
        assert "question_formset" in response.context

        # No meeting should be created
        assert Meeting.objects.count() == 0


class TestViewSecurity:
    """Test view-level security and access control"""

    @pytest.mark.django_db
    def test_create_meeting_requires_login(self, client: Client) -> None:
        """Test that create meeting view requires authentication"""
        response = client.get(reverse("create-meeting"))

        # Should redirect to login
        assert response.status_code == 302
        assert "/login" in response["Location"] or "login" in response["Location"]

    @pytest.mark.django_db
    def test_delete_account_post_only(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test delete account only works with POST"""
        client.force_login(authenticated_user)

        # GET should redirect
        response = client.get(reverse("delete-account"))
        assert response.status_code == 302
        assert response["Location"] == reverse("dashboard")

        # User should still exist
        assert CustomUser.objects.filter(email=authenticated_user.email).exists()

    @pytest.mark.django_db
    def test_successful_account_deletion(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test successful account deletion"""
        client.force_login(authenticated_user)

        response = client.post(reverse("delete-account"))

        # Should redirect to landing
        assert response.status_code == 302
        assert response["Location"] == reverse("landing")

        # User should be deleted
        assert not CustomUser.objects.filter(email=authenticated_user.email).exists()


class TestDashboardAndAccountViews:
    """Test simple authenticated views"""

    @pytest.mark.django_db
    def test_dashboard_requires_authentication(self, client: Client) -> None:
        """Test dashboard redirects unauthenticated users"""
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/login" in response["Location"] or "login" in response["Location"]

    @pytest.mark.django_db
    def test_dashboard_renders_for_authenticated_users(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test dashboard renders correctly for authenticated users"""
        client.force_login(authenticated_user)

        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        assert "director/dashboard.html" in [t.name for t in response.templates]

    @pytest.mark.django_db
    def test_account_requires_authentication(self, client: Client) -> None:
        """Test account page redirects unauthenticated users"""
        response = client.get(reverse("account"))
        assert response.status_code == 302
        assert "/login" in response["Location"] or "login" in response["Location"]

    @pytest.mark.django_db
    def test_account_renders_for_authenticated_users(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        """Test account page renders correctly for authenticated users"""
        client.force_login(authenticated_user)

        response = client.get(reverse("account"))
        assert response.status_code == 200
        assert "director/account.html" in [t.name for t in response.templates]


class TestCreateMeetingMinuteRateLimit:
    def setup_method(self) -> None:
        cache.clear()
        self.ip = "127.0.0.1"
        self.meeting_data = {
            "title": "Test Meeting",
            "description": "Test Description",
            "duration": 30,
            # Formset management data
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "1",
            "form-MAX_NUM_FORMS": "20",
            # Questions
            "form-0-description": "First question?",
            "form-1-description": "Second question?",
        }

    def test_create_meeting_post_rate_limit(
        self, client: Client, authenticated_user: CustomUser
    ) -> None:
        client.force_login(authenticated_user)
        for i in range(3):
            response = client.post(
                path=reverse("create-meeting"),
                data=self.meeting_data,
                REMOTE_ADDR=self.ip,
            )
            assert response.status_code == 302  # Redirected to host live meeting page
        final_response = client.post(
            path=reverse("create-meeting"), data=self.meeting_data, REMOTE_ADDR=self.ip
        )
        assert final_response.status_code == 403  # RATE-LIMITED
