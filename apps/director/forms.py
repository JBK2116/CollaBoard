from django import forms
from django.forms import modelformset_factory
from apps.director.models import Meeting, Question


class CreateMeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting  # The model whose attributes to follow
        fields = [
            "title",
            "description",
            "duration",
        ]
QuestionFormSet = modelformset_factory(
        model = Question,
        fields=["description", "position"],
        extra=1,
        can_delete=True
    )