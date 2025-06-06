from django.shortcuts import render,redirect
from .models import Information
from django.urls import path
from .app_form import LoactionForm
#from . import mqtt_iot
# Create your views here.
def tot_data_list(request):
    data_collected = Information.objects.all()
    context = {"tot_data":data_collected}
    print(context["tot_data"])
    return render(request,"projectApp/tot_data_list.html",context)

def select_data_list(request):
    location = Information.objects.values_list("loc").distinct()
    locations = []
    locations.append(("All","All"))
    data_selected = Information.objects.all()
    for i in location:
        locations.append((i[0],i[0]))
    if request.method == "POST":
        form = LoactionForm(request.POST)
        form.fields['location'].choices = locations
        if form.is_valid():
            select_location = form.cleaned_data['location']
            # query the location
            if not select_location == "All":
                data_selected = data_selected.filter(loc = select_location)
            # query the begin time
            begin_time = form.cleaned_data.get("begin_time")
            if begin_time:
                data_selected = data_selected.filter(date_created__gte = begin_time)
            # query the end time
            end_time = form.cleaned_data.get("end_time")
            if end_time:
                data_selected = data_selected.filter(date_created__lte = end_time)
            context = {"form":form,"select_data":data_selected}
            return render(request,"projectApp/select_data_list.html",context)
    else:
        form = LoactionForm()
        if "clear" in request.GET:
            form.reset()
            context = {"form":form,"select_data":data_selected}
            return redirect(request.path)
        form.fields["location"].choices = locations
    context = {"option":False,"form":form,"select_data":data_selected}
    return render(request,"projectApp/select_data_list.html",context)