import pytest
from django.contrib.auth.hashers import make_password

from apps.base.models import CustomUser


@pytest.fixture
def authenticated_user(db) -> CustomUser:
    return CustomUser.objects.create(
        first_name="John",
        last_name="Doe",
        password=make_password("johndoe123"),
        email="johndoe@gmail.com",
    )
