from django.db import models
from apps.base.models import CustomUser
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.
class Meeting(models.Model):
    director = models.ForeignKey(to=CustomUser, null=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=40, null=False, blank=False)
    description = models.CharField(max_length=300, null=False, blank=False)
    duration = models.IntegerField(
        null=False,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Meeting duration in minutes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Question(models.Model):
    meeting = models.ForeignKey(Meeting, null=False, on_delete=models.CASCADE)
    description = models.CharField(max_length=300, null=False, blank=False)
    position = models.IntegerField(
        null=False, help_text="Question's index position in the meeting"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
