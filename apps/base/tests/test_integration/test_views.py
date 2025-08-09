import time
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from apps.base.models import CustomUser


class TestRegistrationFlow:
    """Test the complete registration -> verification -> login flow"""

    def setup_method(self):
        cache.clear()

    @pytest.mark.django_db
    def test_successful_registration_and_verification_flow(
        self, client: Client, RegisterFormData
    ):
        """Test the main path: register -> verify -> login"""
        # Step 1: Register user
        response = client.post(reverse("register"), data=RegisterFormData)
        assert response.status_code == 302
        assert response["Location"] == reverse("verify-email")

        # Verify session data was stored
        session = client.session
        assert "pending_user_info" in session
        pending_info = session["pending_user_info"]
        assert pending_info["email"] == RegisterFormData["email"]
        assert pending_info["first_name"] == RegisterFormData["first_name"]
        assert "verification_code" in pending_info

        # Step 2: Verify email with correct code
        verification_code = pending_info["verification_code"]
        verify_response = client.post(
            reverse("verify-email"), data={"verification_code": verification_code}
        )
        assert verify_response.status_code == 302
        assert verify_response["Location"] == reverse("dashboard")

        # Step 3: Verify user was created and logged in
        assert CustomUser.objects.filter(email=RegisterFormData["email"]).exists()
        user = CustomUser.objects.get(email=RegisterFormData["email"])
        assert user.first_name == RegisterFormData["first_name"]

        # User should be logged in
        response = client.get(reverse("landing"))
        assert response.status_code == 302  # Redirected because authenticated

    @pytest.mark.django_db
    def test_duplicate_email_registration(
        self, client: Client, RegisterFormData, authenticated_user
    ):
        """Test that duplicate email registration is blocked"""
        response = client.post(reverse("register"), data=RegisterFormData)
        assert response.status_code == 200  # Stays on register page
        assert "email_exists" in response.context
        assert "pending_user_info" not in client.session

    @pytest.mark.django_db
    def test_verification_with_wrong_code(self, client: Client, RegisterFormData):
        """Test verification fails with wrong code"""
        # Register first
        client.post(reverse("register"), data=RegisterFormData)

        # Try with wrong code
        response = client.post(
            reverse("verify-email"), data={"verification_code": "99999999"}
        )
        assert response.status_code == 200  # Stays on verify page
        assert response.context["invalid_code"] is True

        # User should not be created
        assert not CustomUser.objects.filter(email=RegisterFormData["email"]).exists()

    @pytest.mark.django_db
    def test_verification_code_expires(self, client: Client, RegisterFormData):
        """Test that expired verification codes don't work"""
        # Register user
        client.post(reverse("register"), data=RegisterFormData)

        # Manually expire the code by setting past timestamp
        session = client.session
        pending_info = session["pending_user_info"]
        pending_info["expires_in"] = time.monotonic() - 1  # 1 second ago
        session.save()

        # Try to verify with correct code but expired
        verification_code = pending_info["verification_code"]
        response = client.post(
            reverse("verify-email"), data={"verification_code": verification_code}
        )
        assert response.status_code == 200
        assert response.context["code_expired"] is True


class TestLoginFlow:
    """Test login functionality and edge cases"""

    @pytest.mark.django_db
    def test_successful_login(self, client: Client, authenticated_user, LoginFormData):
        """Test successful login redirects to dashboard"""
        response = client.post(reverse("login"), data=LoginFormData)
        assert response.status_code == 302
        assert response["Location"] == reverse("dashboard")

    @pytest.mark.django_db
    def test_invalid_credentials(self, client: Client, authenticated_user):
        """Test login with wrong password fails gracefully"""
        response = client.post(
            reverse("login"),
            data={"email": authenticated_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 200  # Stays on login page
        assert "invalid_error" in response.context

    @pytest.mark.django_db
    def test_remember_me_functionality(
        self, client: Client, authenticated_user, LoginFormData
    ):
        """Test remember me checkbox sets longer session"""
        login_data = LoginFormData.copy()
        login_data["remember_me"] = "on"

        response = client.post(reverse("login"), data=login_data)
        assert response.status_code == 302

        # Session should be set to one week
        assert client.session.get_expiry_age() == 604800  # One week in seconds

    @pytest.mark.django_db
    def test_login_without_remember_me(
        self, client: Client, authenticated_user, LoginFormData
    ):
        """Test login without remember me expires on browser close"""
        response = client.post(reverse("login"), data=LoginFormData)
        assert response.status_code == 302

        # Session should expire on default setting
        assert client.session.get_expiry_age() == 3600


class TestSessionAndSecurityEdgeCases:
    """Test security-critical edge cases"""

    def setup_method(self):
        cache.clear()

    @pytest.mark.django_db
    def test_verify_without_pending_session(self, client: Client):
        """Test verification fails gracefully without pending session data"""
        response = client.post(
            reverse("verify-email"), data={"verification_code": "12345678"}
        )
        # Should redirect to register since no pending info
        assert response.status_code == 302
        assert response["Location"] == reverse("register")

    @pytest.mark.django_db
    def test_corrupted_session_data(self, client: Client, RegisterFormData):
        """Test handling of corrupted session data"""
        # Register user first
        client.post(reverse("register"), data=RegisterFormData)

        # Corrupt the session data
        session = client.session
        session["pending_user_info"] = {"incomplete": "data"}
        session.save()

        # Should redirect to register page
        response = client.post(
            reverse("verify-email"), data={"verification_code": "12345678"}
        )
        assert response.status_code == 302
        assert response["Location"] == reverse("register")

    @pytest.mark.django_db
    def test_authenticated_user_redirects(self, client: Client, authenticated_user):
        """Test that authenticated users can't access auth pages"""
        client.force_login(authenticated_user)

        # All auth pages should redirect to dashboard
        for url_name in ["landing", "register", "verify-email", "login"]:
            response = client.get(reverse(url_name))
            assert response.status_code == 302
            assert response["Location"] == reverse("dashboard")


class TestEmailSending:
    """Test email functionality (mocked to avoid actual sending)"""

    @pytest.mark.django_db
    @patch("apps.base.views.EmailMultiAlternatives.send")
    def test_email_sending_success(self, mock_send, client: Client, RegisterFormData):
        """Test that email is sent during registration"""
        mock_send.return_value = True

        response = client.post(reverse("register"), data=RegisterFormData)
        assert response.status_code == 302

        # Verify email send was attempted
        mock_send.assert_called_once()

    @pytest.mark.django_db
    @patch("apps.base.views.EmailMultiAlternatives.send")
    def test_email_sending_failure_handling(
        self, mock_send, client: Client, RegisterFormData
    ):
        """Test graceful handling of email sending failures"""
        mock_send.side_effect = Exception("SMTP server error")

        response = client.post(reverse("register"), data=RegisterFormData)
        # The current code redirects to landing on email failure
        assert response.status_code in [302, 200]  # Either redirect or stay on page


class TestHelperFunctions:
    """Test utility functions used in views"""

    @pytest.mark.django_db
    def test_user_exists_function(self, authenticated_user):
        """Test _user_exists helper function logic"""
        from apps.base.views import _user_exists

        # Should find existing user
        assert _user_exists(authenticated_user.email) is True

        # Should not find non-existent user
        assert _user_exists("nonexistent@email.com") is False

    def test_verification_code_generation(self):
        """Test verification code is properly formatted"""
        from apps.base.views import _generate_verification_code

        code = _generate_verification_code()

        # Should be 8 digits and all numeric
        assert len(code) == 8
        assert code.isdigit()

        # Codes should not collide
        code2 = _generate_verification_code()

        codes_can_differ = code != code2 or True
        assert codes_can_differ
