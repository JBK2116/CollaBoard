import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.director.models import Meeting, Question


# Create your models here.
class MeetingSession(models.Model):
    id = models.IntegerField(primary_key=True)
    meeting = models.OneToOneField(to=Meeting, on_delete=models.CASCADE)
    current_duration = models.IntegerField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0), MaxValueValidator(3600)],
        help_text="Duration in seconds",
    )
    current_question_index = models.IntegerField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ParticipantSession(models.Model):
    id = models.IntegerField(primary_key=True)
    meeting = models.ForeignKey(to=Meeting, on_delete=models.CASCADE)
    name = models.CharField(null=False, max_length=30, unique=True)
    total_responses = models.IntegerField(
        null=False, default=0, validators=[MinValueValidator(0)]
    )
    sessiontoken = models.CharField(
        null=False,
        max_length=66,
        help_text="Used to identify previous meeting Session by the user",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Response(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    # Relationship Constraints
    meeting = models.ForeignKey(
        to=Meeting, null=False, blank=False, on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        to=Question, null=False, blank=False, on_delete=models.CASCADE
    )
    participant_session = models.ForeignKey(
        to=ParticipantSession, null=True, blank=True, on_delete=models.CASCADE
    )
    response_text = models.CharField(null=False, blank=False, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["question", "created_at"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"Response {self.id} to Question {self.question.position} of meeting {self.meeting.title}"
