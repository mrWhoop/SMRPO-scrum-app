from .models import Task
from bootstrap_modal_forms.forms import BSModalModelForm
from django import forms
from django.contrib.auth.models import User

class TaskModelForm(BSModalModelForm):
    
    class Meta:
        model = Task
        fields = [ 'timeCost', 'description', 'assignedUser', 'userConfirmed']