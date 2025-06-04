from django import forms

class AnswerForm(forms.Form):
    answer = forms.TypedChoiceField(
        label="Is this image AI-generated?",
        choices=[(True, "Yes"), (False, "No")],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=True
    )