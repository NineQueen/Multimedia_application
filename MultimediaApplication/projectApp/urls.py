from django.urls import path
from . import views
urlpatterns = [
    path("totdata",views.tot_data_list),
    path("selectdata",views.select_data_list),
    path("",views.navigation_page),
    path("eventlist",views.add_event),
    path('monitor', views.environmental_monitoring_v3, name='environmental_monitoring_v3'),
]