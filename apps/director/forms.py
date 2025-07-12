from django import forms
from django.forms import modelformset_factory
from apps.director.models import Meeting, Question


class CreateMeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["title", "description", "duration"]
        widgets = {
            'title': forms.TextInput(attrs={
                'maxlength': 40,
                'class': 'form-input',
                'placeholder': 'Enter meeting title...'
            }),
            'description': forms.Textarea(attrs={
                'maxlength': 300,
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Describe your meeting...'
            }),
            'duration': forms.NumberInput(attrs={
                'min': 1,
                'max': 60,
                'class': 'form-input',
                'placeholder': '30'
            })
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or not title.strip():
            raise forms.ValidationError("Meeting title is required")
        return title.strip()

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not description.strip():
            raise forms.ValidationError("Meeting description is required")
        return description.strip()


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["description"]
        widgets = {
            'description': forms.Textarea(attrs={
                'maxlength': 300,
                'class': 'form-textarea question-input',
                'rows': 2,
                'placeholder': 'Enter your question...'
            })
        }

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not description.strip():
            raise forms.ValidationError("Question description is required")
        return description.strip()


# Create formset with better configuration
QuestionFormSet = modelformset_factory(
    model=Question,
    form=QuestionForm,
    fields=["description"],
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=20,
    validate_max=True
)