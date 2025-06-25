from django.forms import ModelForm
from django import forms
from .models import Information,Event

class LocationForm(forms.Form):
    location = forms.ChoiceField(
        choices = [],
        required= False,
        widget= forms.Select(attrs = {"class":"form-control"})
    )
    node_id = forms.ChoiceField(
        choices= [],
        required= False,
        widget= forms.Select(attrs= {"class":"form-control"})
    )
    begin_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local',"class":"form-control custom-control-input"}),
        required= False,
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local',"class":"form-control"}),
        required= False,
        input_formats=['%Y-%m-%dT%H:%M']
    )

    def reset(self):
        for field in self.fields:
            self.fields[field].initial = None
        self.data = {}
        self.is_bound = False

class EventQuery(forms.Form):
    show_past = forms.BooleanField(
        required= False,
        label="Display finished events",
        initial= True
    )
    loc = forms.ChoiceField(
        choices = [],
        required= False,
        widget= forms.Select(attrs = {"class":"form-control"})
    )
    name = forms.CharField(
        required= False,
        widget= forms.TextInput(attrs= {"class":"form-control","maxlength":8})
    )
    instructor = forms.CharField(
        required= False,
        widget= forms.TextInput(attrs= {"class":"form-control","maxlength":20})
    )
    begin_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local',"class":"form-control"}),
        required= False,
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local',"class":"form-control"}),
        required= False,
        input_formats=['%Y-%m-%dT%H:%M']
    )
    def reset(self):
        for field in self.fields:
            self.fields[field].initial = None
        self.data = {}
        self.is_bound = False

class EventForm(forms.ModelForm):
    loc = forms.ChoiceField(
        choices= [],
        widget= forms.Select(attrs= {"class":"form-control"}),
        label="Location"
    )
    class Meta:
        model = Event
        fields = ['begin_time', 'end_time', 'Description',"name","instructor"]
        widgets = {
            'begin_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
            'Description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                }
            ),
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    "maxlength":8,
                }
            ),
            'instructor': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    "maxlength":20,
                }
            ),
        }
        labels = {
            "begin_time":"Begin Time",
            "end_time":"End Time",
            'Description': 'Event Description',
            "instructor":"Instructor",
        }
        input_formats = {
            "begin_time":['%Y-%m-%dT%H:%M'],
            "end_time":['%Y-%m-%dT%H:%M'],
        }
    def reset(self):
        for field in self.fields:
            self.fields[field].initial = None
        self.data = {}
        self.is_bound = False