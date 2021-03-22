from django.conf.urls import include, url

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

admin.autodiscover()

# ce je podcrtan je problem v ide-ju in ne v konfiguraciji
from scrum_app import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^new_story/$', views.new_story_form, name='new_story_form'),
    url(r'^login/$', views.login_user, name='login_user'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^new_project/$', views.new_project_form, name='new_project_form'),
    url(r'^new_sprint/$', views.new_sprint_form, name='new_sprint_form'),
]
