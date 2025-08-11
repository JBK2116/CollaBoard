from typing import Any, cast

from django import forms


# Forms used in the frontend for user authentication
class VerifyEmailForm(forms.Form):
    verification_code = forms.CharField(max_length=8, required=True)

    def clean_verification_code(self) -> str:
        code = self.cleaned_data["verification_code"]
        code = cast(str, code)
        if not code.isdigit():
            raise forms.ValidationError(message="Verification code can only contain digits")
        if len(code) > 8:
            raise forms.ValidationError(message="Verification code must be eight digits")
        return code

class ResetPasswordEmailForm(forms.Form):
    email = forms.EmailField(required=True)

class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput)

    def clean_password2(self) -> str:
        password1: str = self.cleaned_data["password1"]
        password2: str = self.cleaned_data["password2"]
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(message="Passwords don't match")
        return password2
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
