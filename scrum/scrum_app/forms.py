from .models import Task, Story
from bootstrap_modal_forms.forms import BSModalModelForm
from django import forms
from django.contrib.auth.models import User

class TaskModelForm(BSModalModelForm):
    
    class Meta:
        model = Task
        fields = ['timeCost' , 'description', 'assignedUser']


class StoryModelForm(BSModalModelForm):

    class Meta:
        model = Story
        fields = ['name','description','priority','businessValue', 'timeCost','timeSpent','comment','developmentStatus']