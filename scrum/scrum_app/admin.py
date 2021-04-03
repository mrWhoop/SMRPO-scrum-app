from django.contrib import admin
from .models import Project, Sprint, DevTeamMember, Story, Task, LastLogin, Post


# Register your models here.
admin.site.register(Project)
admin.site.register(Sprint)
admin.site.register(DevTeamMember)
admin.site.register(Story)
admin.site.register(Task)
admin.site.register(LastLogin)
admin.site.register(Post)