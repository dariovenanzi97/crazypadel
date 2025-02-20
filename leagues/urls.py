from django.urls import path
from . import views

app_name = 'leagues'

urlpatterns = [
    # League management
    path('', views.league_list, name='list'),
    path('create/', views.create_league, name='create'),
    path('<int:league_id>/', views.league_detail, name='detail'),
    path('<int:league_id>/join/', views.join_league, name='join'),
    path('join-by-code/', views.join_by_code, name='join_by_code'),
    
    # Match management (questi percorsi rimangono per retrocompatibilità)
    path('<int:league_id>/matches/create/', views.create_match, name='create_match'),
    path('<int:league_id>/matches/<int:match_id>/', views.match_detail, name='match_detail'),
    path('<int:league_id>/matches/<int:match_id>/edit/', views.edit_match, name='edit_match'),
    path('<int:league_id>/matches/<int:match_id>/delete/', views.delete_match, name='delete_match'),
]