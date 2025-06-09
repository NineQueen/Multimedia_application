from django.urls import path
from . import views
urlpatterns = [
    path('', views.index),
    path('temp_data', views.temp_data, name = 'temp_data'),
    path("classroom",views.class_index)
]