from django.forms import ModelForm
from django import forms
from .models import Information

class LoactionForm(forms.Form):
    location = forms.ChoiceField(
        choices = [],
        widget= forms.Select(attrs = {"class":"form-control"})
    )
    begin_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required= False,
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required= False,
        input_formats=['%Y-%m-%dT%H:%M']
    )

    def reset(self):
        for field in self.fields:
            self.fields[field].initial = None
        self.data = {}
        self.is_bound = False