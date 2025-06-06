from django.shortcuts import render
from .models import Information
from .app_form import LoactionForm
from . import mqtt_iot
# Create your views here.
def tot_data_list(request):
    data_collected = Information.objects.all()
    context = {"tot_data":data_collected}
    print(context["tot_data"])
    return render(request,"projectApp/tot_data_list.html",context)

def select_data_list(request):
    location = Information.objects.values_list("loc").distinct()
    locations = []
    for i in location:
        locations.append((i[0],i[0]))
    if request.method == "POST":
        form = LoactionForm(request.POST)
        form.fields['location'].choices = locations
        if form.is_valid():
            select_location = form.cleaned_data['location']
            print(select_location)
            context = {"option":True}
            return render(request,"projectApp/select_data_list.html",context)
    else:
        form = LoactionForm()
        form.fields["location"].choices = locations
    context = {"option":False,"form":form}
    return render(request,"projectApp/select_data_list.html",context)