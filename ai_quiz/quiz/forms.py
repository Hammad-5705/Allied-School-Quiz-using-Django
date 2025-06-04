from django import forms

class AnswerForm(forms.Form):
    answer = forms.ChoiceField(
        choices=[(True, 'Yes (AI)'), (False, 'No (Not AI)')],
        widget=forms.RadioSelect
    )
