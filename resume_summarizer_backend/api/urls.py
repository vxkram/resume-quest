from django.contrib import admin
from django.urls import path, include  # Include is necessary to include app-level URLs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('resume_summarizer_backend.urls')),  # Assuming the app is called 'resume_summarizer_backend'
]
