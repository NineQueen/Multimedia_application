from django.shortcuts import render,redirect
from .models import Information,Event
from django.urls import path
from .app_form import LocationForm,EventForm
from django.db.models import Avg,Max,Min,Count,FloatField
from django.db.models.functions import Round
from django.utils import timezone
from . import mqtt_iot
# Create your views here.
def tot_data_list(request):
    data_collected = Information.objects.all()
    context = {"tot_data":data_collected}
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
    location = Information.objects.values_list("loc").distinct().order_by("loc")
    locations = []
    locations.append((None,"All"))
    node_id = Information.objects.values_list("node_id").distinct().order_by("node_id")
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
            context["raw_data"] = context["raw_data"].order_by("-date_created")
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
    context["raw_data"] = context["raw_data"].order_by("-date_created")
    context["form"] = form
    return render(request,"projectApp/select_data_list.html",context)

def check_valid(loc,begin_time,end_time):
    events = Event.objects.filter(loc = loc)
    events = events.filter(begin_time__lte = end_time)
    events = events.filter(end_time__gte = begin_time)
    if len(events) > 0:
        return False
    return True

def add_event(request):
    #Event.objects.all().delete()
    location = Information.objects.values_list("loc").distinct().order_by("loc")
    locations = []
    locations.append((None,"--"))
    for i in location:
        locations.append((i[0],i[0]))
    events = Event.objects.all()
    context = {"events":events}
    if "id" in request.GET:
        try:
            event_id = Event.objects.filter(id = int(request.GET["id"]))[0]
            context["id"] = event_id
            return render(request,"projectApp/event_list.html",context)
        except Exception as e:
            print(e)
    context["type"] = "success"
    if request.method == "POST":
        try:
            form = EventForm(request.POST)
            form.fields['loc'].choices = locations
            if form.is_valid():
                loc = form.cleaned_data['loc']
                begin_time = form.cleaned_data.get("begin_time")
                end_time = form.cleaned_data.get("end_time")
                if begin_time>=end_time:
                    raise AssertionError("Error! The start time must be earlier than the end time!")
                if not check_valid(loc,begin_time,end_time):
                    raise AssertionError("Error! The classroom has been occupied!")
                event = form.save(commit=False)
                event.loc = loc
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
    form.fields['loc'].choices = locations
    context["form"] = form
    return render(request,"projectApp/add_event.html",context)

def check_empty(loc,time):
    event = Event.objects.filter(loc = loc)
    event = event.filter(begin_time__lte = time)
    event = event.filter(end_time__gte = time)
    return event

def navigation_page(request):
    all_result = get_series_data()
    location = Information.objects.values_list("loc").distinct().order_by("loc")
    locations = []
    for i in location:
        time = timezone.now()
        event = check_empty(i[0],time)
        empty = False
        if len(event) == 0:
            empty = True
        context = {
            "env" : Information.objects.filter(loc = i[0]).order_by("-date_created")[0],
            "empty": empty,
        }
        if not empty:
            context["detail"] = event[0]
        locations.append(context)
    tot_temp = 0
    tot_hum = 0
    tot_snd = 0
    tot_light = 0
    for i in locations:
        tot_light += i["env"].light
        tot_snd += i["env"].snd
        tot_hum += i["env"].hum
        tot_temp += i["env"].temp
    tot_light /= len(locations)
    tot_snd /= len(locations)
    tot_hum /= len(locations)
    tot_temp /= len(locations)
    tot_light = "{:.2f}".format(tot_light)
    tot_snd = "{:.2f}".format(tot_snd)
    tot_temp = "{:.2f}".format(tot_temp)
    tot_hum = "{:.2f}".format(tot_hum)
    all_result = {
        "temp" : tot_temp,
        "hum":tot_hum,
        "light":tot_light,
        "snd" : tot_snd,
    }
    context = {"all":all_result,"locs":locations}
    return render(request,"index.html",context)

def environmental_monitoring_v3(request):
    data = Information.objects.all().order_by('-date_created')
    return render(request, 'projectApp/env-monitor-v3.html', {
        'data': data
    })