from django.urls import path
from . import views
from .views import EventApiView
urlpatterns = [
    path("totdata",views.tot_data_list),
    path("selectdata",views.select_data_list),
    path("",views.navigation_page),
    path("eventlist",views.add_event),
    path('monitor', views.environmental_monitoring_v3, name='environmental_monitoring_v3'),
    path('api/events/', EventApiView.as_view(), name='event_api'),
    path('map/', views.show_map, name='map-view'),
    path('map/image/', views.get_map_image, name='map-image'),
    path("log",views.log_list)
]