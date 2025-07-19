import uuid

from django.db import models

from apps.director.models import Meeting, Question


# Create your models here.
class Response(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    session_id = models.CharField(
        max_length=100, help_text="Session ID for anonymous participant", unique=True
    )
    # Relationship Constraints
    meeting = models.ForeignKey(
        to=Meeting, null=False, blank=False, on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        to=Question, null=False, blank=False, on_delete=models.CASCADE
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
