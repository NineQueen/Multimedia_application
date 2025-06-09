from django.shortcuts import render,redirect
from .models import Information,Event
from django.urls import path
from .app_form import LocationForm,EventForm
from django.db.models import Avg,Max,Min,Count,FloatField
from django.db.models.functions import Round
#from . import mqtt_iot
# Create your views here.
def tot_data_list(request):
    data_collected = Information.objects.all()
    context = {"tot_data":data_collected}
    print(context["tot_data"])
    return render(request,"projectApp/tot_data_list.html",context)

#Return the series data's average 
def get_series_data(input_node_id = None,input_loc = None,input_begin_time = None,input_end_time = None):
    try:
        data_selected = Information.objects.all()
        if input_node_id:
            data_selected = data_selected.filter(node_id = input_node_id)
        if input_loc:
            data_selected = data_selected.filter(loc = input_loc)
        if input_begin_time:
            data_selected = data_selected.filter(date_created__gte = input_begin_time)
        if input_end_time:
            data_selected = data_selected.filter(date_created__lte = input_end_time)
    except BaseException as e:
        print("Error at get_series_data()",e)
        return get_series_data()
    temp_result = data_selected.aggregate(avg = Round(Avg("temp", output_field=FloatField())),max = Max("temp"),min = Min("temp"))
    hum_result = data_selected.aggregate(avg = Round(Avg("hum", output_field=FloatField())),max = Max("hum"),min = Min("hum"))
    snd_result = data_selected.aggregate(avg = Round(Avg("snd", output_field=FloatField())),max = Max("snd"))
    light_result = data_selected.aggregate(avg = Round(Avg("light", output_field=FloatField())),max = Max("light"))
    cnt = data_selected.aggregate(Count("id"))
    #return pattern
    results = {
        "raw_data": data_selected,
        "temp" : temp_result,
        "hum" : hum_result,
        "snd" : snd_result,
        "light" : light_result,
        "cnt" : cnt 
    }
    return results


def select_data_list(request):
    location = Information.objects.values_list("loc").distinct()
    locations = []
    locations.append((None,"All"))
    node_id = Information.objects.values_list("node_id").distinct()
    node_id_list = []
    node_id_list.append((None,"All"))
    data_selected = Information.objects.all()
    for i in location:
        locations.append((i[0],i[0]))
    for i in node_id:
        node_id_list.append((i[0],i[0]))
    if request.method == "POST":
        form = LocationForm(request.POST)
        form.fields['location'].choices = locations
        form.fields["node_id"].choices = node_id_list
        if form.is_valid():
            # query the location
            select_location = form.cleaned_data['location']
            # query the node_id
            select_node_id = form.cleaned_data["node_id"]
            # query the begin time
            begin_time = form.cleaned_data.get("begin_time")
            # query the end time
            end_time = form.cleaned_data.get("end_time")
            context = get_series_data(select_node_id,select_location,begin_time,end_time)
            print("check",context)
            context["form"] = form
            return render(request,"projectApp/select_data_list.html",context)
    else:
        form = LocationForm()
        if "clear" in request.GET:
            form.reset()
            context = {"form":form,"select_data":data_selected}
            return redirect(request.path)
        form.fields["location"].choices = locations
        form.fields["node_id"].choices = node_id_list
    context = get_series_data()
    context["form"] = form
    return render(request,"projectApp/select_data_list.html",context)

def check_valid(loc,begin_time,end_time):
    events = Event.objects.filter(loc = loc)
    print(events)
    events = Event.objects.filter(begin_time__lte = end_time)
    print(events)
    events = Event.objects.filter(end_time__gte = begin_time)
    if len(events) > 0:
        return False
    return True

def add_event(request):
    #Event.objects.all().delete()
    events = Event.objects.all()
    context = {"events":events}
    context["type"] = "success"
    if request.method == "POST":
        try:
            form = EventForm(request.POST)
            if form.is_valid():
                loc = form.cleaned_data.get("loc")
                begin_time = form.cleaned_data.get("begin_time")
                end_time = form.cleaned_data.get("end_time")
                if begin_time>=end_time:
                    raise AssertionError("Error! The start time must be earlier than the end time!")
                if not check_valid(loc,begin_time,end_time):
                    raise AssertionError("Error! The classroom has been occupied!")
                event = form.save()
                return redirect(request.path)
        except Exception as e:
            print(e)
            form = EventForm()
            context["type"] = "fail"
            context["error_message"] = e
    else:
        form = EventForm()
        if "clear" in request.GET:
            form.reset()
            return redirect(request.path)
    context["form"] = form
    return render(request,"projectApp/add_event.html",context)
            
def navigation_page(request):
    all_result = get_series_data()
    location = Information.objects.values_list("loc").distinct()
    print(location)
    locations = []
    for i in location:
        locations.append(Information.objects.filter(loc = i[0]).order_by("-date_created")[0])
    print(locations)
    context = {"all":all_result,"locs":locations}
    return render(request,"index.html",context)