from .models import Task, Story, Project
from bootstrap_modal_forms.forms import BSModalModelForm
from django import forms
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

class TaskModelForm(BSModalModelForm):
    
    class Meta:
        model = Task
        fields = ['timeCost' , 'description', 'assignedUser']


class StoryModelForm(BSModalModelForm):

    class Meta:
        model = Story
        fields = ['name','description','priority','businessValue', 'timeCost','timeSpent','comment','developmentStatus']


class DocumentationForm(forms.ModelForm):

    documentation = RichTextField()

    class Meta:
        model = Project
        fields = ['documentation']
