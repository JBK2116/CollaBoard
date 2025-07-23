import uuid
from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.base.models import CustomUser


class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access_code = models.CharField(max_length=8, null=False, blank=False, unique=True)
    director = models.ForeignKey(to=CustomUser, null=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=40, null=False, blank=False)
    description = models.CharField(max_length=300, null=False, blank=False)
    total_questions_asked = models.PositiveIntegerField(
        null=False, default=0, help_text="Amount of questions asked during the meeting"
    )
    duration = models.IntegerField(
        null=False,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Meeting duration in minutes",
    )
    duration_in_seconds = models.PositiveIntegerField(
        null=False, default=0, help_text="Meeting duration in seconds"
    )
    participants = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title

    def format_duration_in_seconds(self) -> str:
        total_seconds = self.duration_in_seconds

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        return " ".join(parts)


class Question(models.Model):
    meeting = models.ForeignKey(
        Meeting, null=False, on_delete=models.CASCADE, related_name="questions"
    )
    description = models.CharField(max_length=300, null=False, blank=False)
    position = models.PositiveIntegerField(
        null=False, help_text="Question's index position in the meeting"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["meeting", "position"]
        ordering = ["position"]

    def __str__(self) -> str:
        return f"Q{self.position}: {self.description[:50]}..."

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Auto-assign position if not provided
        if not self.position:
            last_question = (
                Question.objects.filter(meeting=self.meeting)
                .order_by("-position")
                .first()
            )
            self.position = (last_question.position + 1) if last_question else 1
        super().save(*args, **kwargs)
