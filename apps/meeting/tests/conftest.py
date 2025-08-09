import pytest
from django.contrib.auth.hashers import make_password

from apps.base.models import CustomUser
from apps.director.models import Meeting, Question
from apps.meeting.models import Response


# ---------- Fixtures ----------
@pytest.fixture
def user(db):
    """Create a test user."""
    return CustomUser.objects.create(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password=make_password("password123"),
    )


@pytest.fixture
def meeting(user) -> Meeting:
    """Create a meeting linked to the test user."""
    return Meeting.objects.create(
        summarized_meeting={},
        access_code="ABC12345",
        director=user,
        title="Team Sync",
        description="Weekly team sync meeting",
        duration=30,
        duration_in_seconds=1800,
    )


@pytest.fixture
def question(meeting) -> Question:
    """Create a question for the meeting."""
    return Question.objects.create(
        meeting=meeting, description="How are we doing?", position=1
    )


@pytest.fixture
def response(meeting, question) -> Response:
    return Response.objects.create(
        meeting=meeting, question=question, response_text="All good!"
    )
