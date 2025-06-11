from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from projectApp.models import Information,Event
from projectApp.views import get_series_data,check_empty
from django.utils import timezone
# Create your views here.
def index(request):
    data = get_series_data()
    context = {"data":data,}
    return render(request, 'dashboard/index.html',context)
def temp_data(request):
    try:
        if "loc" in request.GET:
            print(request.GET["loc"])
            events = Information.objects.filter(loc = request.GET["loc"])
        elif "id" in request.GET:
            print("check eventid")
            event_id = int(request.GET["id"])
            this_event = Event.objects.filter(id = event_id)[0]
            print("Get Loc",this_event.loc)
            events = get_series_data(input_loc=this_event.loc,input_begin_time=this_event.begin_time,input_end_time=this_event.end_time)["raw_data"]
            print(events)
        else:
            events = Information.objects.order_by("-date_created")[0:500]
    except BaseException as e:
        events = Information.objects.all().order_by("-date_created")[0:500]
        print("Error!",e)
    data = serializers.serialize('json', events) #Translating Django models into JSON formats
    return JsonResponse(data, safe=False) #Returns a string that contains an array object

def class_index(request):
    if request.GET:
        print("check")
        context = {"loc":request.GET["loc"],"data" : get_series_data(input_loc=request.GET['loc'])}
        time = timezone.now()
        event = check_empty(request.GET["loc"],time)
        empty = "Using"
        if len(event) == 0:
            empty = "Empty"
            event = Event.objects.filter(loc = request.GET["loc"]).filter(begin_time__gte = time).order_by("begin_time")
            if len(event) != 0:
                event = event[0]
                empty = "Upcoming"
            context["event"] = event
        else:
            context["event"] = event[0]
        context["status"] = empty
        return render(request, 'dashboard/index_classroom.html',context)
    print("No request")
    context = {"data":get_series_data()}
    return render(request, "dashboard/index.html",context)

def history_index(request):
    if request.GET:
        event_id = request.GET["id"]
        event = Event.objects.filter(id = int(event_id))[0]
        context = {"loc":event.name,"data":get_series_data(input_loc=event.loc,input_begin_time=event.begin_time,input_end_time=event.end_time)}
        context["event"] = event
        return render(request,"dashboard/index_history.html",context)