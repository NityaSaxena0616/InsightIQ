from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_data, name='upload'),
    path('analytics/', views.analytics, name='analytics'),
    path('reports/', views.reports, name='reports'),
]