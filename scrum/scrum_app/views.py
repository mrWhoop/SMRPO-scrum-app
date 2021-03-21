from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Project

def index(request):

    text = 'Hello World!'

    return render(request, 'home.html', context={'text': text, 'string': 'string', 'activate_home':'active'})

def new_story_form(request):
    return render(request, 'new_story.html', context={'activate_newstory':'active'})


def new_project_form(request):
    users =  get_user_model().objects.all()
    if request.method == 'POST':
        project_name =request.POST["project_name"]
        product_owner = request.POST["product_owner"]
        scrum_master = request.POST["scrum_master"]
        project = Project(projectName=project_name, product_owner=product_owner, scrum_master=scrum_master)
        project.save()
        
    return render(request,'new_project.html', context={'activate_newproject':'active',  'users':users} )

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)      
            login(request,user)
            return HttpResponseRedirect('/')
            
    else:
        form = AuthenticationForm()
        
    return render(request, "login.html", {'form':form})

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/login/')  

