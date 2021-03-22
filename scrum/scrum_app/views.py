from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Sprint, Story, Project, DevTeamMember
from django.contrib.auth.models import User

import sys

def index(request):

    text = 'Hello World!'

    return render(request, 'home.html', context={'text': text, 'string': 'string', 'activate_home':'active'})

def new_story_form(request):
    users =  get_user_model().objects.all()
    #print(Project.objects.all(), file=sys.stderr)
    projects = Project.objects.all()
    sprints = Sprint.objects.all()
    success = False
    name_exists = False

    if request.method == 'POST':
        story_name = request.POST["story_name"];
        story_description = request.POST["story_description"];
        story_priority = request.POST["story_priority"];
        story_bussines_value = request.POST["story_bussines_value"]
        time_cost = request.POST["time_cost"]
        time_spent = request.POST["time_spent"]
        asignee = request.POST["asignee"]
        user_confirmed = request.POST.get('user_confirmed', "") == "on"
        comment = request.POST['comment']
        story_status = request.POST['story_status']
        project = request.POST['project']
        sprint = request.POST['sprint']
        story, created = Story.objects.get_or_create(name=story_name,
                                                     description=story_description,
                                                     priority=story_priority,
                                                     businessValue=story_bussines_value,
                                                     timeCost=time_cost,
                                                     timeSpent=time_spent,
                                                     assignedUser_id=asignee,
                                                     userConfirmed=user_confirmed,
                                                     comment=comment,
                                                     developmentStatus=story_status,
                                                     project_id=project,
                                                     sprint_id=sprint)
        if not created:
            name_exists = not name_exists
        else:
            story.save()
            success = not success



    return render(request,    'new_story.html', 
                  context={   'activate_newstory': 'active', 
                              'users': users,
                              'projects': projects,
                              'success': success,
                              'sprints': sprints,
                              'name_exists':name_exists
                              })


def new_project_form(request):
    users =  get_user_model().objects.all()
    success = False
    name_exists = False
    if request.method == 'POST':
        project_name =request.POST["project_name"]
        product_owner = request.POST["product_owner"]
        product_owner = User.objects.get(username=product_owner)
        scrum_master = request.POST["scrum_master"]
        scrum_master = User.objects.get(username=scrum_master)
        project, created = Project.objects.get_or_create(projectName=project_name, product_owner=product_owner, scrum_master=scrum_master)
        if created == False:
            name_exists = True
        else:
            project.save()
            for dev_team_member in request.POST.getlist("developers"):
                user = User.objects.get(username=dev_team_member)
                dev_team_member = DevTeamMember(userId=user, projectId=project)
                dev_team_member.save()
            success = True
        
    return render(request,    'new_project.html', 
                  context={   'activate_newproject':'active', 
                              'users':users,
                              'success': success,
                              'name_exists':name_exists
                              })

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

