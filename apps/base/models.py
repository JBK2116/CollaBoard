from typing import Any, Optional

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager["CustomUser"]):
    """
    Defines how the User(or the model to which attached)
    will create users and superusers.
    """

    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "CustomUser":
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError("The Email must be set")  # Email is necessary
        email = self.normalize_email(email)  # lowercase the domain
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hash raw password and set
        user.save()
        return user

    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "CustomUser":
        """
        Create and save a superuser with the given email and password.
        Extra fields are added to indicate that the user is staff, active,
        and indeed a superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # type: ignore[assignment]  # Not needed in the application
    email = models.EmailField(max_length=254, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"  # email is now the login field of the model.
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]
    objects = CustomUserManager()  # type: ignore
    # objects here is needed to ensure that
    # Custom User manage is the one used when creating CustomUser models.

    def __str__(self) -> str:
        return super().__str__()
