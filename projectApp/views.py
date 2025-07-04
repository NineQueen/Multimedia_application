from django.shortcuts import render,redirect
from .models import Information,Event,Warning,WarningMessage
from django.urls import path
from .app_form import LocationForm,EventForm,EventQuery
from django.db.models import Avg,Max,Min,Count,FloatField
from datetime import timedelta
from django.db.models.functions import Round
from django.utils import timezone
from django.http import JsonResponse
from django.views import View
import json
#from . import mqtt_iot,request
from django.shortcuts import render
from django.views.static import serve
from django.conf import settings
import os
from django.http import HttpResponse, Http404
from pathlib import Path
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def show_map(request):
    """显示地图页面"""
    return render(request, 'map/map.html')

def get_map_image(request):
    """直接从projectApp的模板目录返回地图图片"""
    image_path = Path(settings.BASE_DIR) / 'projectApp' / 'templates' / 'map' / 'map.png'
    
    if not image_path.exists():
        raise Http404("地图图片不存在")
    
    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')
# Create your views here.
def tot_data_list(request):
    Information.objects.filter(loc = "W411").delete()
    Information.objects.filter(loc = "W412").delete()
    Warning.objects.all().delete()
    WarningMessage.objects.all().delete()
    Information.objects.filter(temp = 100).delete()
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
    form = LocationForm()
    form.fields['location'].choices = locations
    form.fields["node_id"].choices = node_id_list
    data_selected = Information.objects.all()
    for i in location:
        locations.append((i[0],i[0]))
    for i in node_id:
        node_id_list.append((i[0],i[0]))
    if request.method == "GET":
        if "clear" in request.GET:
            form.reset()
            context = {"form":form,"select_data":data_selected}
            return redirect(request.path)
        form = LocationForm(request.GET)
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
            raw_data = get_series_data(select_node_id,select_location,begin_time,end_time)
            context = dict()
            context["raw_data"] = raw_data["raw_data"].order_by("-date_created")
            context["form"] = form
            #return render(request,"projectApp/select_data_list.html",context)
        form.fields["location"].choices = locations
        form.fields["node_id"].choices = node_id_list
    if form.is_valid():
        cpage =  raw_data
    else:
        cpage = get_series_data()
    paginator = Paginator(cpage["raw_data"].order_by("-date_created"),50)
    page = request.GET.get("page")
    try:
        raw_data = paginator.page(page)
    except PageNotAnInteger:
        raw_data = paginator.page(1)
    except EmptyPage:
        raw_data = paginator.page(paginator.num_pages)
    context = dict()
    context["raw_data"] = raw_data
    context["form"] = form
    try:
        filter_params = request.GET.copy()
        filter_params.pop("page",None)
        filter_params  = filter_params.urlencode
    except BaseException as e:
        filter_params = None
        print("Error!",e)
    context["other_params"] = filter_params
    return render(request,"projectApp/select_data_list.html",context)

def check_valid(loc,begin_time,end_time):
    events = Event.objects.filter(loc = loc)
    events = events.filter(begin_time__lte = end_time)
    events = events.filter(end_time__gte = begin_time)
    if len(events) > 0:
        return False
    return True

def log_list(request):
    if "id" in request.GET:
        warning = Warning.objects.filter(id = int(request.GET["id"]))[0]
        if "check" in request.GET:
            print("check")
            warning.status = True
            warning.save()
            return redirect(request.path+"?id={}".format(int(request.GET["id"])))
        context = {"id":warning}
        return render(request,"projectApp/log_detail.html",context)
    warnings = Warning.objects.order_by("status")
    context = {"warning":warnings}
    return render(request,"projectApp/log_list.html",context)

def add_event(request):
    #Event.objects.all().delete()
    location = Information.objects.values_list("loc").distinct().order_by("loc")
    locations = []
    locations.append((None,"--"))
    for i in location:
        locations.append((i[0],i[0]))
    events = Event.objects.all().order_by("end_time")
    events_status = []
    tot_events = []
    time = timezone.now()
    for event in events:
        ans = get_series_data(None,event.loc,event.begin_time,event.end_time)
        this_event = {
            "id":event.id,
            "name":event.name,
            "loc":event.loc,
            "instructor":event.instructor,
            "begin_time":event.begin_time,
            "end_time":event.end_time,
            "Description":event.Description,
            "ans":ans
        }
        if event.end_time < time:
                this_event["status"] = "Finish"
        elif time < event.begin_time:
                this_event["status"] = "Upcoming"
        elif event.begin_time <= time <= event.end_time:
                this_event["status"] = "Ongoing"
        tot_events.append(this_event)
    context = {"entrys":tot_events}
    if "id" in request.GET:
        print("check")
        try:
            event_id = Event.objects.filter(id = int(request.GET["id"]))[0]
            ans = {
                "id":event_id.id,
                "name":event_id.name,
                "loc":event_id.loc,
                "instructor":event_id.instructor,
                "begin_time":event_id.begin_time,
                "end_time":event_id.end_time,
                "Description":event_id.Description,
            }
            if ans["end_time"] < time:
                ans["status"] = "Finish"
            elif time < ans["begin_time"]:
                ans["status"] = "Upcoming"
            elif ans["begin_time"] <= time <= ans["end_time"]:
                ans["status"] = "Ongoing"
            context["id"] = ans
            formQ = EventQuery(prefix="query")
            formQ.fields['loc'].choices = locations
            if request.method == "POST":
                formQ = EventQuery(request.POST,prefix="query")
                formQ.fields['loc'].choices = locations
                if formQ.is_valid():
                    loc = formQ.cleaned_data["loc"]
                    begin_time = formQ.cleaned_data.get("begin_time")
                    end_time = formQ.cleaned_data.get("end_time")
                    instructor = formQ.cleaned_data["instructor"]
                    name = formQ.cleaned_data['name']
                    time = timezone.now()
                    show_past = formQ.cleaned_data.get("show_past")
                    if loc:
                        events = events.filter(loc = loc)
                    if begin_time:
                        events = events.filter(begin_time__gte = begin_time)
                    if end_time:
                        events = events.filter(end_time__lte = end_time)
                    if instructor:
                        events = events.filter(instructor = instructor)
                    if name:
                        events = events.filter(name = name)
                    if not show_past:
                        events = events.filter(end_time__gte = time)
                    tot_events = []
                    for event in events:
                        ans_tot = get_series_data(None,event.loc,event.begin_time,event.end_time)
                        this_event = {
                            "id":event.id,
                            "name":event.name,
                            "loc":event.loc,
                            "instructor":event.instructor,
                            "begin_time":event.begin_time,
                            "end_time":event.end_time,
                            "Description":event.Description,
                            "ans":ans_tot,
                        }
                        if event.end_time < time:
                                this_event["status"] = "Finish"
                        elif time < event.begin_time:
                                this_event["status"] = "Upcoming"
                        elif event.begin_time <= time <= event.end_time:
                                this_event["status"] = "Ongoing"
                        tot_events.append(this_event)
                    context["entrys"] = tot_events
            if "clear" in request.GET:
                return redirect(request.path+"?id={}".format(request.GET["id"]))
            context["formQ"] = formQ
            return render(request,"projectApp/event_list.html",context)
        except Exception as e:
            print("Error",e)
    context["type"] = "success"
    form = EventForm(prefix="add")
    formQ = EventQuery(prefix="query")
    formQ.fields['loc'].choices = locations
    form.fields['loc'].choices = locations
    if request.method == "POST":
        try:
            if 'form_type' in request.POST:
                if request.POST["form_type"] == 'add':
                    form = EventForm(request.POST,prefix="add")
                    form.fields['loc'].choices = locations
                    if form.is_valid():
                        print("form check")
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
                    else:
                        print("check form",form)
                if request.POST["form_type"] == "query":
                    formQ = EventQuery(request.POST,prefix="query")
                    formQ.fields['loc'].choices = locations
                    if formQ.is_valid():
                        loc = formQ.cleaned_data["loc"]
                        begin_time = formQ.cleaned_data.get("begin_time")
                        end_time = formQ.cleaned_data.get("end_time")
                        instructor = formQ.cleaned_data["instructor"]
                        name = formQ.cleaned_data['name']
                        show_past = formQ.cleaned_data.get("show_past")
                        if loc:
                            events = events.filter(loc = loc)
                        if begin_time:
                            events = events.filter(begin_time__gte = begin_time)
                        if end_time:
                            events = events.filter(end_time__lte = end_time)
                        if instructor:
                            events = events.filter(instructor = instructor)
                        if name:
                            events = events.filter(name = name)
                        if not show_past:
                            events = events.filter(end_time__gte = time)
                        tot_events = []
                        for event in events:
                            ans_tot = get_series_data(None,event.loc,event.begin_time,event.end_time)
                            this_event = {
                                "id":event.id,
                                "name":event.name,
                                "loc":event.loc,
                                "instructor":event.instructor,
                                "begin_time":event.begin_time,
                                "end_time":event.end_time,
                                "Description":event.Description,
                                "ans":ans_tot,
                            }
                            if event.end_time < time:
                                    this_event["status"] = "Finish"
                            elif time < event.begin_time:
                                    this_event["status"] = "Upcoming"
                            elif event.begin_time <= time <= event.end_time:
                                    this_event["status"] = "Ongoing"
                            tot_events.append(this_event)
                        context = {"entrys":tot_events}
        except Exception as e:
            print("Error at add_event!",e)
            context["type"] = "fail"
            context["error_message"] = e
    else:
        if "clear" in request.GET:
            return redirect(request.path)
    context["form"] = form
    context["formQ"] =formQ
    return render(request,"projectApp/add_event.html",context)

def check_empty(loc,time):
    event = Event.objects.filter(loc = loc)
    event = event.filter(begin_time__lte = time)
    event = event.filter(end_time__gte = time)
    return event

def navigation_page(request):
    warning = Warning.objects.filter(status = False)
    warning_tag = len(warning)
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
    context = {"all":all_result,"locs":locations,"check":warning_tag}
    return render(request,"index.html",context)

def environmental_monitoring_v3(request):
    one_day_ago = timezone.now() - timedelta(days=1)
    data = Information.objects.filter(date_created__gte = one_day_ago).order_by('-date_created')
    return render(request, 'projectApp/env-monitor-v3.html', {
        'data': data
    })

class EventApiView(View):
    def get(self, request):
        try:
            loc = request.GET.get('loc')
            start_date = request.GET.get('start')
            end_date = request.GET.get('end')
            
            # Convert string dates to datetime objects
            if start_date:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')
            
            # Filter events
            events = Event.objects.filter(loc=loc)
            if start_date:
                events = events.filter(end_time__gte=start_date)
            if end_date:
                events = events.filter(begin_time__lte=end_date)
            
            # Prepare events data
            events_data = []
            current_time = timezone.now()
            
            for event in events:
                status = "Upcoming"
                if event.end_time < current_time:
                    status = "Finished"
                elif event.begin_time <= current_time <= event.end_time:
                    status = "Ongoing"
                
                # 添加更多事件详情
                events_data.append({
                    'id': event.id,
                    'title': f"{event.name}",
                    'start': event.begin_time.isoformat(),
                    'end': event.end_time.isoformat(),
                    'extendedProps': {
                        'loc': event.loc,
                        'instructor': event.instructor,
                        'description': event.Description,
                        'status': status,
                        'event_id': event.id
                    }
                })
            
            return JsonResponse(events_data, safe=False)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)