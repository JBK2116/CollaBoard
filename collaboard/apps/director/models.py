import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.base.models import CustomUser

# Create your models here.


class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    director = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, null=False, blank=False
    )
    access_code = models.CharField(max_length=8, null=False, blank=False)
    title = models.CharField(max_length=60, null=False, blank=False)
    description = models.CharField(max_length=200, null=False, blank=False)
    duration = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MinValueValidator(
                15,
                message="Meeting Duration must be greater than or equal to 15 minutes",
            ),
            MaxValueValidator(120, message="Meeting Duration cannot exceed 2 hours"),
        ],
    )
    published = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(null=True)

    # Below are object instance methods
    def __str__(self) -> str:
        return f"ID: {self.id}|Director Name: {self.director.get_full_name()} |Meeting Name: {self.title} |description: {self.description} |Duration (minutes): {self.duration}| questions: {self.get_question_count()}"

    def get_question_count(self) -> int:
        return Question.objects.filter(meeting=self).count()


class Question(models.Model):
    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, null=False, blank=False
    )
    description = models.CharField(max_length=150, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Belongs to Meeting: {self.meeting.title}| Description: {self.description}| Total Responses: {self.get_response_count()} "

    def get_response_count(self) -> int:
        return Response.objects.filter(question=self).count()


class Response(models.Model):
    user = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL
    )
    # User deletion logic will be implemented elsewhere
    question = models.ForeignKey(
        Question, null=False, blank=False, on_delete=models.CASCADE
    )
    answer = models.TextField()  # Max length enforcement will be handled elsewhere
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Responding to question: {self.question.description} of meeting {self.question.meeting.title}"
