import pytest
from django.db import IntegrityError

from apps.base.models import CustomUser
from apps.director.forms import CreateMeetingForm, QuestionForm
from apps.director.models import Meeting, Question
from apps.director.views import generate_access_code


class TestQuestionModel:
    """Test Question model behavior, especially position auto-assignment"""

    @pytest.mark.django_db
    def test_question_position_auto_assignment(self, authenticated_user: CustomUser):
        """Test that positions are automatically assigned correctly"""
        meeting = Meeting.objects.create(
            director=authenticated_user,
            title="Test Meeting",
            description="Test",
            duration=30,
            access_code="12345678",
        )

        # Create questions without specifying position
        q1 = Question.objects.create(meeting=meeting, description="First?")
        q2 = Question.objects.create(meeting=meeting, description="Second?")
        q3 = Question.objects.create(meeting=meeting, description="Third?")

        # Positions should be auto-assigned
        assert q1.position == 1
        assert q2.position == 2
        assert q3.position == 3

    @pytest.mark.django_db
    def test_question_position_unique_constraint(self, authenticated_user: CustomUser):
        """Test that duplicate positions in same meeting are prevented"""
        meeting = Meeting.objects.create(
            director=authenticated_user,
            title="Test Meeting",
            description="Test",
            duration=30,
            access_code="12345678",
        )

        Question.objects.create(meeting=meeting, description="First?", position=1)

        # Should raise IntegrityError for duplicate position
        with pytest.raises(IntegrityError):
            Question.objects.create(
                meeting=meeting, description="Duplicate?", position=1
            )


class TestMeetingModel:
    """Test Meeting model methods and behavior"""

    @pytest.mark.django_db
    def test_format_duration_in_seconds_various_durations(
        self, authenticated_user: CustomUser
    ):
        """Test duration formatting for different time periods"""
        meeting = Meeting.objects.create(
            director=authenticated_user,
            title="Test Meeting",
            description="Test",
            duration=30,
            access_code="12345678",
        )

        test_cases = [
            (0, "0 seconds"),
            (1, "1 second"),
            (30, "30 seconds"),
            (60, "1 minute"),
            (90, "1 minute 30 seconds"),
            (3600, "1 hour"),
            (3661, "1 hour 1 minute 1 second"),
            (7320, "2 hours 2 minutes"),
            (7380, "2 hours 3 minutes"),
        ]

        for seconds, expected in test_cases:
            meeting.duration_in_seconds = seconds
            assert meeting.format_duration_in_seconds() == expected


class TestAccessCodeGeneration:
    """Test access code generation utility"""

    def test_access_code_format(self):
        """Test access code is properly formatted"""
        code = generate_access_code()

        assert len(code) == 8
        assert code.isdigit()
        assert all(c in "0123456789" for c in code)

    def test_access_code_uniqueness_probability(self):
        """Test that codes are reasonably unique (statistical test)"""
        # Generate multiple codes and check for uniqueness
        codes = set()
        for _ in range(100):
            code = generate_access_code()
            codes.add(code)

        # Should have high uniqueness (allow for small chance of collision)
        assert len(codes) >= 95  # 95% uniqueness is reasonable


class TestForms:
    """Test form validation logic"""

    def test_meeting_form_whitespace_handling(self):
        """Test that form properly trims whitespace"""
        form_data = {
            "title": "  Test Meeting  ",
            "description": "  Test Description  ",
            "duration": 30,
        }

        form = CreateMeetingForm(data=form_data)
        assert form.is_valid()

        # Should be trimmed
        assert form.cleaned_data["title"] == "Test Meeting"
        assert form.cleaned_data["description"] == "Test Description"

    def test_meeting_form_boundary_values(self):
        """Test form validation at boundary values"""
        # Test minimum duration
        form_data = {
            "title": "Test Meeting",
            "description": "Test Description",
            "duration": 1,  # Minimum allowed
        }
        form = CreateMeetingForm(data=form_data)
        assert form.is_valid()

        # Test maximum duration
        form_data["duration"] = 60  # Maximum allowed
        form = CreateMeetingForm(data=form_data)
        assert form.is_valid()

        # Test invalid duration
        form_data["duration"] = 0  # Below minimum
        form = CreateMeetingForm(data=form_data)
        assert not form.is_valid()

    def test_question_form_validation(self):
        """Test question form validation"""
        # Valid question
        form = QuestionForm(data={"description": "Valid question?"})
        assert form.is_valid()

        # Empty question
        form = QuestionForm(data={"description": ""})
        assert not form.is_valid()

        # Whitespace-only question
        form = QuestionForm(data={"description": "   "})
        assert not form.is_valid()
