from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from projectApp.models import Information
from projectApp.views import get_series_data

# Create your views here.
def index(request):
    data = get_series_data()
    context = {"data":data}
    return render(request, 'dashboard/index.html',context)
def temp_data(request):
    try:
        if request.GET:
            print(request.GET["loc"])
            events = Information.objects.filter(loc = request.GET["loc"])
        else:
            events = Information.objects.all()
    except BaseException as e:
        events = Information.objects.all()
    data = serializers.serialize('json', events) #Translating Django models into JSON formats
    return JsonResponse(data, safe=False) #Returns a string that contains an array object

def class_index(request):
    if request.GET:
        print("check")
        context = {"loc":request.GET["loc"],"data" : get_series_data(input_loc=request.GET['loc'])}
        print("Get request",request.GET)
        return render(request, 'dashboard/index_classroom.html',context)
    print("No request")
    context = {"data":get_series_data()}
    return render(request, "dashboard/index.html",context)