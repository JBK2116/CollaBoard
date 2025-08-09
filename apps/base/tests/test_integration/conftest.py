import pytest
from django.contrib.auth.hashers import make_password

from apps.base.models import CustomUser


@pytest.fixture
def RegisterFormData() -> dict[str, str]:
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@gmail.com",
        "password1": "johndoe123",
        "password2": "johndoe123",
    }


@pytest.fixture
def VerificationCode() -> dict[str, str]:
    return {"verification_code": "12345678"}


@pytest.fixture
def LoginFormData() -> dict[str, str]:
    return {
        "email": "johndoe@gmail.com",
        "password": "johndoe123",
    }


@pytest.fixture
def authenticated_user(db: None) -> CustomUser:
    return CustomUser.objects.create(
        first_name="John",
        last_name="Doe",
        password=make_password("johndoe123"),
        email="johndoe@gmail.com",
    )
