from datetime import timedelta
from uuid import UUID

import pytest
from django.utils import timezone

from apps.director.models import Meeting, Question
from apps.meeting.models import Response


# ---------- Tests ----------
@pytest.mark.django_db
def test_create_response_success(meeting: Meeting, question: Question) -> None:
    """Valid Response should save and link correctly."""
    response = Response.objects.create(
        meeting=meeting, question=question, response_text="All good!"
    )
    assert isinstance(response.id, UUID)
    assert response.meeting == meeting
    assert response.question == question
    assert response.response_text == "All good!"


@pytest.mark.skip(reason="Not properly implemented yet")
def test_response_requires_text(meeting: Meeting, question: Question) -> None:
    """Response without text should raise an error."""
    with pytest.raises(Exception):
        Response.objects.create(meeting=meeting, question=question, response_text="")


@pytest.mark.django_db
def test_str_method(meeting: Meeting, question: Question) -> None:
    """__str__ method should return expected format."""
    response = Response.objects.create(
        meeting=meeting, question=question, response_text="Fine"
    )
    expected = f"Response {response.id} to Question 1 of meeting Team Sync"
    assert str(response) == expected


@pytest.mark.django_db
def test_ordering_by_created_at(meeting: Meeting, question: Question) -> None:
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
def test_foreign_key_cascade(meeting: Meeting, question: Question) -> None:
    """Deleting a meeting should delete related responses (cascade)."""
    response = Response.objects.create(
        meeting=meeting, question=question, response_text="Linked"
    )
    meeting.delete()
    assert not Response.objects.filter(id=response.id).exists()


# ---------- Index / Filtering Tests ----------
@pytest.mark.django_db
def test_filter_by_question_and_created_at(
    meeting: Meeting, question: Question
) -> None:
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
