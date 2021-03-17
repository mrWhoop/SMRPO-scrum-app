from django.conf.urls import include, url

from django.conf import settings
from django.conf.urls.static import static

# ce je podcrtan je problem v ide-ju in ne v konfiguraciji
from scrum_app import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]
