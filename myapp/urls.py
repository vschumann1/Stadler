# myapp/urls.py
from django.urls import path
from . import views


# Define the URL patterns for the application, linking each route to a view function in views.py
urlpatterns = [

    path('login/', views.login_view, name='login'),


    path('logout/', views.logout, name='logout'),


    path('', views.dashboard, name='dashboard'),


    path('projekterstellung/', views.projekterstellung, name='projekterstellung'),


    path('project-details/<str:project_name>/', views.project_details, name='project_details'),


    path('benchmarking/<str:project_name>/', views.benchmarking, name='benchmarking'),


    path('benchmarking/<str:project_name>/<str:filter_din>/', views.benchmarking, name='benchmarking_filtered'),


    path('export-csv/<str:project_name>/<str:filter_din>/', views.export_csv, name='export_csv'),


    path('workflow/<str:project_name>/', views.workflow, name='workflow'),


    path('lcc-taetigkeiten/<str:project_name>/', views.display_taetigkeiten_data, name='display_taetigkeiten_data'),

    # Neue URL für LCC-Tätigkeiten2 hinzufügen
    path('lcc-taetigkeiten2/<str:project_name>/', views.display_taetigkeiten2_data, name='display_taetigkeiten2_data'),
]
