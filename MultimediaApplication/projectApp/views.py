from django.shortcuts import render,redirect
from .models import Information
from django.urls import path
from .app_form import LoactionForm
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
            data_selected = data_selected.filter(data_created__lte = input_end_time)
    except BaseException as e:
        print("Error at get_series_data()",e)
        return
    temp_result = data_selected.aggregate(avg = Round(Avg("temp", output_field=FloatField()), 2),max = Max("temp"),min = Min("temp"))
    hum_result = data_selected.aggregate(avg = Round(Avg("hum", output_field=FloatField()), 2),max = Max("hum"),min = Min("hum"))
    cnt = data_selected.aggregate(Count("id"))
    #return pattern
    results = {
        "raw_data": data_selected,
        "temp" : temp_result,
        "hum" : hum_result,
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
        form = LoactionForm(request.POST)
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
            context["form"] = form
            return render(request,"projectApp/select_data_list.html",context)
    else:
        form = LoactionForm()
        if "clear" in request.GET:
            form.reset()
            context = {"form":form,"select_data":data_selected}
            return redirect(request.path)
        form.fields["location"].choices = locations
        form.fields["node_id"].choices = node_id_list
    context = get_series_data()
    context["form"] = form
    return render(request,"projectApp/select_data_list.html",context)