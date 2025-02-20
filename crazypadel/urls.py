from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('leagues/', include('leagues.urls')),
    path('', RedirectView.as_view(pattern_name='leagues:list', permanent=False)),
]