from django.forms import ModelForm
from django import forms
from .models import Information

class LoactionForm(forms.Form):
    location = forms.ChoiceField(
        label="Select the location",
        choices = [],
        widget= forms.Select(attrs = {"class":"form-control"})
    )