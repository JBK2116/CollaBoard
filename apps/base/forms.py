from django import forms
from typing import Any


# Forms used in the frontend for user authentication
class UserRegisterForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    password1 = forms.CharField(
        max_length=128, required=True, widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        max_length=128, required=True, widget=forms.PasswordInput
    )

    def clean_password2(self) -> Any:
        """
        Custom clean method.
        Primarily used to ensure that password1 and password2
        are equal.
        """
        password1 = self.cleaned_data["password1"]
        password2 = self.cleaned_data["password2"]
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(message="Passwords don't match")
        return password2


class UserLoginForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
    password = forms.CharField(
        max_length=128, required=True, widget=forms.PasswordInput
    )
