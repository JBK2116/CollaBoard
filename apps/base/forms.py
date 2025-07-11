from django import forms

# Forms used in the frontend for user authentication
class UserRegisterForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    password1 = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput)

class UserLoginForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True)
    password = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput)
