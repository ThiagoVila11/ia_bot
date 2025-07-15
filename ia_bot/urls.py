from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # ou o nome correto do seu app
    path('api/', include('core.urls')),
]
