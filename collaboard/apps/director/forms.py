from django import forms
from django.forms import formset_factory


class MeetingForm(forms.Form):
    title = forms.CharField(
        max_length=60,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'meetingTitle',
            'placeholder': 'Enter meeting title',
            'maxlength': '60',
            'required': True,
        })
    )
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'id': 'meetingDescription',
            'placeholder': 'Optional: Describe what this meeting is about...',
            'rows': 3,
            'maxlength': '200',
            'required': True,
        })
    )
    duration = forms.ChoiceField(
        choices=[
            ('', 'Select duration'),
            ('15', '15 minutes'),
            ('30', '30 minutes'),
            ('45', '45 minutes'),
            ('60', '1 hour'),
            ('90', '1.5 hours'),
            ('120', '2 hours'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'meetingDuration',
            'required': True,
        })
    )

class QuestionForm(forms.Form):
    text = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control question-input',
            'placeholder': 'Enter your question...',
            'maxlength': '150',
            'required': True,
        })
    )

QuestionFormSet = formset_factory(QuestionForm, extra=1, max_num=20)
