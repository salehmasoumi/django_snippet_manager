from django.urls import path
from . import views

app_name = 'snippets'

urlpatterns = [
    path('', views.snippet_list, name='list'),
    path('new/', views.snippet_create, name='create'),
    # specific action patterns MUST come before the generic <slug>/ pattern
    # (URL-ordering bug documented in PROJECT_PATTERNS.md section 13)
    path('<slug:slug>/edit/', views.snippet_edit, name='edit'),
    path('<slug:slug>/delete/', views.snippet_delete, name='delete'),
    path('<slug:slug>/', views.snippet_detail, name='detail'),
]
