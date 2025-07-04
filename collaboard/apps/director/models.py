from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.base.models import CustomUser

# Create your models here.


class Meeting(models.Model):
    id = models.IntegerField(primary_key=True)
    director = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, null=False, blank=False
    )
    title = models.CharField(max_length=60, null=False, blank=False)
    description = models.CharField(max_length=200, null=False, blank=False)
    duration = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MinValueValidator(
                1,
                message="Meeting Duration must be greater than or equal to 15 minutes",
            ),
            MaxValueValidator(120, message="Meeting Duration cannot exceed 2 hours"),
        ],
    )
    questions = ArrayField(
        models.CharField(max_length=150, null=False, blank=False), default=list
    )

    # Below are object instance methods
    def __str__(self) -> str:
        return f"ID: {self.id}|Director Name: {self.director.get_full_name()} |Meeting Name: {self.title} |description: {self.description} |Duration (minutes): {self.duration}| questions: {self.get_question_count()}"

    # Get the total amount of questions in a meeting
    def get_question_count(self) -> int:
        return len(self.questions or [])
