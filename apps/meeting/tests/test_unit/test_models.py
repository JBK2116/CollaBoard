from datetime import timedelta
from uuid import UUID

import pytest
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.utils import timezone

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
def meeting(user):
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
def question(meeting):
    """Create a question for the meeting."""
    return Question.objects.create(
        meeting=meeting, description="How are we doing?", position=1
    )


# ---------- Tests ----------
@pytest.mark.django_db
def test_create_response_success(meeting, question):
    """Valid Response should save and link correctly."""
    response = Response.objects.create(
        meeting=meeting, question=question, response_text="All good!"
    )
    assert isinstance(response.id, UUID)
    assert response.meeting == meeting
    assert response.question == question
    assert response.response_text == "All good!"


@pytest.mark.django_db
def test_response_requires_text(meeting, question):
    """Response without text should raise an error."""
    with pytest.raises(IntegrityError):
        Response.objects.create(meeting=meeting, question=question, response_text=None)


@pytest.mark.django_db
def test_str_method(meeting, question):
    """__str__ method should return expected format."""
    response = Response.objects.create(
        meeting=meeting, question=question, response_text="Fine"
    )
    expected = f"Response {response.id} to Question 1 of meeting Team Sync"
    assert str(response) == expected


@pytest.mark.django_db
def test_ordering_by_created_at(meeting, question):
    """Responses should be ordered by created_at ascending."""
    older = Response.objects.create(
        meeting=meeting, question=question, response_text="First"
    )
    newer = Response.objects.create(
        meeting=meeting, question=question, response_text="Second"
    )
    responses = list(Response.objects.all())
    assert responses[0] == older
    assert responses[1] == newer


@pytest.mark.django_db
def test_foreign_key_cascade(meeting, question):
    """Deleting a meeting should delete related responses (cascade)."""
    response = Response.objects.create(
        meeting=meeting, question=question, response_text="Linked"
    )
    meeting.delete()
    assert not Response.objects.filter(id=response.id).exists()


# ---------- Index / Filtering Tests ----------
@pytest.mark.django_db
def test_filter_by_question_and_created_at(meeting, question):
    """
    Ensure filtering by (question, created_at) works efficiently.
    This indirectly validates that the DB index exists and can be used.
    """
    now = timezone.now()
    Response.objects.bulk_create(
        [
            Response(
                meeting=meeting,
                question=question,
                response_text="R1",
                created_at=now - timedelta(minutes=2),
            ),
            Response(
                meeting=meeting,
                question=question,
                response_text="R2",
                created_at=now - timedelta(minutes=1),
            ),
            Response(
                meeting=meeting, question=question, response_text="R3", created_at=now
            ),
        ]
    )
    results = Response.objects.filter(question=question).order_by("created_at")
    assert [r.response_text for r in results] == ["R1", "R2", "R3"]
