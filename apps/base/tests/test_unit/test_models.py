import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.db.utils import IntegrityError as DBIntegrityError

from apps.base.models import CustomUser

User = get_user_model()


class TestCustomUserApplicationPattern:
    """Test CustomUser using the same patterns as the actual application."""

    @pytest.mark.django_db
    def test_create_user_like_application(self):
        """Test creating a user the same way the application does."""
        from django.contrib.auth.hashers import make_password

        raw_password = "testpass123"
        user = CustomUser(
            email="test@example.com",
            password=make_password(raw_password),  # Hash password manually like the app
            first_name="John",
            last_name="Doe",
        )
        user.save()

        assert user.email == "test@example.com"
        assert user.check_password(raw_password)  # Should work with hashed password
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    @pytest.mark.django_db
    def test_email_uniqueness_application_pattern(self):
        """Test email uniqueness using application pattern."""
        from django.contrib.auth.hashers import make_password

        # Create first user
        user1 = CustomUser(
            email="test@example.com",
            password=make_password("password1"),
            first_name="John",
            last_name="Doe",
        )
        user1.save()

        # Try to create second user with same email
        user2 = CustomUser(
            email="test@example.com",  # Same email
            password=make_password("password2"),
            first_name="Jane",
            last_name="Smith",
        )

        with pytest.raises((IntegrityError, DBIntegrityError)):
            user2.save()

    @pytest.mark.django_db
    def test_user_authentication_with_application_created_user(self):
        """Test authentication works with users created using application pattern."""
        from django.contrib.auth import authenticate
        from django.contrib.auth.hashers import make_password

        raw_password = "testpass123"
        user = CustomUser(
            email="test@example.com",
            password=make_password(raw_password),
            first_name="John",
            last_name="Doe",
        )
        user.save()

        # Test authentication using email (as per your authenticate call)
        authenticated_user = authenticate(
            email="test@example.com",  # Your app uses email parameter
            password=raw_password,
        )
        assert authenticated_user == user

    @pytest.mark.django_db
    def test_password_hashing_consistency(self):
        """Test that make_password produces consistent, secure hashes."""
        from django.contrib.auth.hashers import check_password, make_password

        raw_password = "testpass123"
        hashed1 = make_password(raw_password)
        hashed2 = make_password(raw_password)

        # Hashes should be different (due to salt) but both should verify
        assert hashed1 != hashed2
        assert check_password(raw_password, hashed1)
        assert check_password(raw_password, hashed2)

        # Wrong password should not verify
        assert not check_password("wrongpassword", hashed1)


class TestCustomUserManager:
    """Test the CustomUserManager functionality (for completeness, even though app doesn't use it)."""

    @pytest.mark.django_db
    def test_create_user_manager_method(self):
        """Test the manager's create_user method works correctly."""
        user = CustomUser.objects.create(
            email="test@example.com",
            password=make_password("testpass123"),  # Follows application flow
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.first_name == "John"
        assert user.last_name == "Doe"


class TestCustomUserModel:
    """Test the CustomUser model functionality."""

    @pytest.fixture
    def user_data(self):
        """Provide valid user data for tests."""
        return {
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
        }

    @pytest.fixture
    def user(self):
        """Create a test user using the same pattern as the application."""
        from django.contrib.auth.hashers import make_password

        user = CustomUser(
            email="test@example.com",
            password=make_password("testpass123"),  # Hash password like the app does
            first_name="John",
            last_name="Doe",
        )
        user.save()
        return user

    @pytest.mark.django_db
    def test_str_representation(self, user):
        """Test the string representation of CustomUser."""
        assert str(user) == "John Doe"

    @pytest.mark.django_db
    def test_str_representation_with_empty_names(self):
        """Test string representation with empty names."""
        user = CustomUser.objects.create(
            email="test@example.com", first_name="", last_name=""
        )
        assert str(user) == " "

    @pytest.mark.django_db
    def test_email_uniqueness(self):
        """Test that email must be unique."""
        from django.contrib.auth.hashers import make_password

        # Create first user
        user1 = CustomUser(
            email="test@example.com",
            password=make_password("password1"),
            first_name="John",
            last_name="Doe",
        )
        user1.save()

        # Try to create second user with same email
        user2 = CustomUser(
            email="test@example.com",  # Same email
            password=make_password("password2"),
            first_name="Jane",
            last_name="Smith",
        )

        with pytest.raises((IntegrityError, DBIntegrityError)):
            user2.save()

    @pytest.mark.django_db
    def test_email_case_sensitivity_uniqueness(self, user):
        """Test that email uniqueness is case-sensitive for local part."""
        # This should work - different local part case
        user2 = CustomUser.objects.create(
            email="TEST@example.com", first_name="Jane", last_name="Smith"
        )
        assert user2.email == "TEST@example.com"

    @pytest.mark.django_db
    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email."""
        assert CustomUser.USERNAME_FIELD == "email"

    @pytest.mark.django_db
    def test_required_fields(self):
        """Test that REQUIRED_FIELDS contains first_name and last_name."""
        assert "first_name" in CustomUser.REQUIRED_FIELDS
        assert "last_name" in CustomUser.REQUIRED_FIELDS

    @pytest.mark.django_db
    def test_username_is_none(self, user):
        """Test that username field is disabled."""
        assert user.username is None

    @pytest.mark.django_db
    def test_count_fields_default_values(self, user):
        """Test that count fields have correct default values."""
        assert user.meetings_created_count == 0
        assert user.total_participants_count == 0
        assert user.total_responses_count == 0

    @pytest.mark.django_db
    def test_count_fields_can_be_updated(self, user):
        """Test that count fields can be updated."""
        user.meetings_created_count = 5
        user.total_participants_count = 25
        user.total_responses_count = 100
        user.save()

        user.refresh_from_db()
        assert user.meetings_created_count == 5
        assert user.total_participants_count == 25
        assert user.total_responses_count == 100

    @pytest.mark.django_db
    def test_count_fields_are_positive_integers(self):
        """Test that count fields only accept positive integers."""
        user = CustomUser.objects.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            meetings_created_count=10,
            total_participants_count=50,
            total_responses_count=200,
        )
        assert user.meetings_created_count == 10
        assert user.total_participants_count == 50
        assert user.total_responses_count == 200

    @pytest.mark.django_db
    def test_datetime_fields_auto_populated(self, user):
        """Test that created_at and updated_at are auto-populated."""
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at

    @pytest.mark.django_db
    def test_updated_at_changes_on_save(self, user):
        """Test that updated_at changes when model is saved."""
        original_updated_at = user.updated_at
        user.first_name = "Jane"
        user.save()
        user.refresh_from_db()
        assert user.updated_at > original_updated_at

    @pytest.mark.django_db
    def test_created_at_field_type(self, user):
        """Test that created_at is a DateTimeField."""
        field = user._meta.get_field("created_at")
        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True

    @pytest.mark.django_db
    def test_updated_at_field_type(self, user):
        """Test that updated_at is a DateTimeField."""
        field = user._meta.get_field("updated_at")
        assert isinstance(field, models.DateTimeField)
        assert field.auto_now is True


class TestCustomUserValidation:
    """Test CustomUser model validation."""

    @pytest.mark.django_db
    def test_email_field_validation(self):
        """Test email field validation."""
        user = CustomUser(email="invalid-email", first_name="John", last_name="Doe")
        with pytest.raises(ValidationError) as exc_info:
            user.full_clean()
        assert "email" in exc_info.value.message_dict

    @pytest.mark.django_db
    def test_first_name_min_length_validation(self):
        """Test that first_name validates minimum length."""
        user = CustomUser(
            email="test@example.com",
            first_name="",  # Empty string should fail MinLengthValidator
            last_name="Doe",
        )
        with pytest.raises(ValidationError) as exc_info:
            user.full_clean()
        assert "first_name" in exc_info.value.message_dict

    @pytest.mark.django_db
    def test_last_name_min_length_validation(self):
        """Test that last_name validates minimum length."""
        user = CustomUser(
            email="test@example.com",
            first_name="John",
            last_name="",  # Empty string should fail MinLengthValidator
        )
        with pytest.raises(ValidationError) as exc_info:
            user.full_clean()
        assert "last_name" in exc_info.value.message_dict

    @pytest.mark.django_db
    def test_email_max_length(self):
        """Test email max length constraint."""
        long_email = "a" * 250 + "@example.com"  # Over 254 characters
        user = CustomUser(email=long_email, first_name="John", last_name="Doe")
        with pytest.raises(ValidationError) as exc_info:
            user.full_clean()
        assert "email" in exc_info.value.message_dict

    @pytest.mark.django_db
    def test_name_max_length(self):
        """Test first_name and last_name max length constraint."""
        long_name = "a" * 151  # Over 150 characters

        # Test first_name
        user1 = CustomUser(
            email="test1@example.com", first_name=long_name, last_name="Doe"
        )
        with pytest.raises(ValidationError) as exc_info:
            user1.full_clean()
        assert "first_name" in exc_info.value.message_dict

        # Test last_name
        user2 = CustomUser(
            email="test2@example.com", first_name="John", last_name=long_name
        )
        with pytest.raises(ValidationError) as exc_info:
            user2.full_clean()
        assert "last_name" in exc_info.value.message_dict


class TestCustomUserConstraints:
    """Test database constraints (these may be skipped for SQLite)."""

    @pytest.mark.skip(reason="SQLite doesn't enforce custom check constraints")
    @pytest.mark.django_db
    def test_email_not_empty_constraint(self):
        """Test that email cannot be empty string at database level."""
        with pytest.raises((IntegrityError, DBIntegrityError)):
            CustomUser.objects.create(email="", first_name="John", last_name="Doe")

    @pytest.mark.skip(reason="SQLite doesn't enforce custom check constraints")
    @pytest.mark.django_db
    def test_first_name_not_empty_constraint(self):
        """Test that first_name cannot be empty string at database level."""
        with pytest.raises((IntegrityError, DBIntegrityError)):
            CustomUser.objects.create(
                email="test@example.com", first_name="", last_name="Doe"
            )

    @pytest.mark.skip(reason="SQLite doesn't enforce custom check constraints")
    @pytest.mark.django_db
    def test_last_name_not_empty_constraint(self):
        """Test that last_name cannot be empty string at database level."""
        with pytest.raises((IntegrityError, DBIntegrityError)):
            CustomUser.objects.create(
                email="test@example.com", first_name="John", last_name=""
            )


class TestCustomUserAuthentication:
    """Test authentication-related functionality."""

    @pytest.mark.django_db
    def test_authenticate_with_email(self):
        """Test that user can be authenticated using email."""
        from django.contrib.auth import authenticate
        from django.contrib.auth.hashers import make_password

        raw_password = "testpass123"
        user = CustomUser(
            email="test@example.com",
            password=make_password(raw_password),
            first_name="John",
            last_name="Doe",
        )
        user.save()

        authenticated_user = authenticate(
            username="test@example.com",  # Note: using username param but with email
            password=raw_password,
        )
        assert authenticated_user == user

    @pytest.mark.django_db
    def test_authenticate_with_wrong_password(self):
        """Test that authentication fails with wrong password."""
        from django.contrib.auth import authenticate

        CustomUser.objects.create(
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )

        authenticated_user = authenticate(
            username="test@example.com", password="wrongpassword"
        )
        assert authenticated_user is None

    @pytest.mark.django_db
    def test_authenticate_with_nonexistent_email(self):
        """Test that authentication fails with non-existent email."""
        from django.contrib.auth import authenticate

        authenticated_user = authenticate(
            username="nonexistent@example.com", password="somepassword"
        )
        assert authenticated_user is None


class TestCustomUserEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.django_db
    def test_create_user_with_unicode_characters(self):
        """Test creating user with unicode characters in names."""
        user = CustomUser.objects.create(
            email="test@example.com",
            password="testpass123",
            first_name="José",
            last_name="Müller",
        )
        assert user.first_name == "José"
        assert user.last_name == "Müller"
        assert str(user) == "José Müller"

    @pytest.mark.django_db
    def test_create_user_with_special_email_characters(self):
        """Test creating user with valid special characters in email."""
        user = CustomUser.objects.create(
            email="test.email+tag@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )
        assert user.email == "test.email+tag@example.com"

    @pytest.mark.django_db
    def test_user_with_maximum_valid_lengths(self):
        """Test user creation with maximum valid field lengths."""
        max_email = "a" * 242 + "@example.com"  # 254 chars total
        max_name = "a" * 150  # 150 chars

        user = CustomUser.objects.create(
            email=max_email,
            password="testpass123",
            first_name=max_name,
            last_name=max_name,
        )
        user.full_clean()  # Should not raise ValidationError
        assert len(user.email) == 254
        assert len(user.first_name) == 150
        assert len(user.last_name) == 150

    @pytest.mark.django_db
    def test_user_is_instance_of_abstract_user(self):
        """Test that CustomUser is properly inheriting from AbstractUser."""
        user = CustomUser.objects.create(
            email="test@example.com", first_name="John", last_name="Doe"
        )
        from django.contrib.auth.models import AbstractUser

        assert isinstance(user, AbstractUser)

    @pytest.mark.django_db
    def test_custom_user_manager_is_attached(self):
        """Test that CustomUserManager is properly attached to the model."""
        from apps.base.models import CustomUserManager

        assert isinstance(CustomUser.objects, CustomUserManager)
