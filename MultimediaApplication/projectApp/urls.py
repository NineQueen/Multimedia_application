from django.urls import path
from . import views

urlpatterns = [
    path("totdata",views.tot_data_list),
    path("selectdata",views.select_data_list),
    path("",views.navigation_page)
]