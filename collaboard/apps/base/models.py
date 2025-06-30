from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    REQUIRED_FIELDS = ["first_name", "last_name", "email"]
