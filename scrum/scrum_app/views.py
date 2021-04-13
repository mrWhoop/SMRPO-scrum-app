import datetime, pytz

import json
from django.db.models.functions import Lower
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Sprint, Story, Project, DevTeamMember, Task, LastLogin, Post, TimeSpent
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core import serializers
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from bootstrap_modal_forms.generic import BSModalUpdateView
from .forms import TaskModelForm
from django.template.loader import render_to_string



import sys

def index(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = user.last_login
        try:
            lastLogin = LastLogin.objects.get(user_id=request.user.id)
            last_login_time = lastLogin.lastLoginTime
        except:
            pass
        projects_devs_qs = {Project.objects.filter(id=devTeamMember.projectId_id) for devTeamMember in DevTeamMember.objects.filter(userId_id=user)}
        projects_devs = []
        for project_dev in projects_devs_qs:
            projects_devs.append(project_dev[0])
        projects_qs = {Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user) )}
        projects =[]
        for project in projects_qs:
            if len(project) > 0:
                projects.append(project[0])
        projects = list(set(projects_devs) | set(projects))
        return render(request, 'home.html', context={'projects': projects,
                                                    'activate_home':'active',
                                                     'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def project(request):
    if request.user.is_authenticated:

        project_id = request.GET.get('id')
        print(project_id)
        project = Project.objects.get(id=project_id)
        
        posts = project.getPosts().order_by('-time_posted')

    

        notProductOwner = True
        isScrumMaster = project.scrum_master_id == request.user.id
        # check product owner
        if project.product_owner_id == request.user.id:
            notProductOwner = False

        stories = Story.objects.filter(project=project).order_by(Lower('developmentStatus').desc())

        today = datetime.date.today()

        sprints = Sprint.objects.filter(project=project).filter(start__gte=today)

        ended_sprints = Sprint.objects.filter(project=project).filter(end__lte=today)

        velocityLeft = 0
        if len(sprints) < 1:
            sprints = None
        else:
            sprints = sprints[0]

            velocityLeft = sprints.expectedSpeed
            sprintStories = Story.objects.filter(sprint=sprints)
            for story in sprintStories:
                velocityLeft -= story.timeCost


        if request.method == 'POST':
            velocityCheck = velocityLeft
            for name, value in request.POST.items():
                if name == 'csrfmiddlewaretoken':
                    continue
                field, story_id = name.split("_")
                if field == 'timecost' and value != 'None':
                    StoryObject = Story.objects.get(id=int(story_id))
                    StoryObject.timeCost = value
                    StoryObject.save()

                if field == 'sprint' and value != 'None':
                    StoryObject = Story.objects.get(id=int(story_id))
                    velocityCheck -= StoryObject.timeCost
                    if velocityCheck < 0:
                        return render(request, 'project.html',
                                      context={'project': project, 'stories': stories, 'sprints': sprints,
                                               'activate_home': 'active', 'velocityLeft': velocityLeft, 'velocityExceeded': True, 'notProductOwner': notProductOwner, 'isScrumMaster':isScrumMaster})
                    StoryObject.sprint_id = value
                    StoryObject.save()

                if field == 'status' and value != 'None':
                    StoryObject = Story.objects.get(id=int(story_id))
                    StoryObject.developmentStatus = value
                    StoryObject.save()


        return render(request, 'project.html', context={'project': project, 'stories': stories, 'sprints': sprints, 'activate_home':'active', 'velocityLeft': velocityLeft, 'velocityExceeded': False, 'notProductOwner': notProductOwner, 'isScrumMaster':isScrumMaster, 'posts':posts, 'ended_sprints': ended_sprints})
    else:
        return HttpResponseRedirect('/login')

def story(request):
    if request.user.is_authenticated:
        user_is_product_owner = False
        story_id = request.GET.get('id')
        story = Story.objects.get(id=story_id)
        tasks = Task.objects.filter(story=story)
        times = []
        
        for task in tasks:
            curr_time = 0
            for time in task.timeSpent:
                curr_time += time.time_spent
            times.append(round(curr_time/3600,3))
        print(times)
        sprint = story.sprint
        sprint_active = True

        utc = pytz.UTC
        if sprint == None or utc.localize(datetime.datetime.today()) > sprint.end:
            sprint_active = False
        
        project = story.project
        product_owner = project.product_owner
        if request.user == product_owner:
            user_is_product_owner = True
        zipped = zip(tasks, times)
        return render(request,'story.html', context={'story':story,'tasks':tasks, 'sprint_active':sprint_active,'user_is_product_owner':user_is_product_owner, 'tasks_times':zipped})
    else:
        return HttpResponseRedirect('/login')

def new_story_form(request):

    if request.user.is_authenticated:
        user = user = get_user_model().objects.get(id=request.user.id)
        #projects = Project.objects.filter(product_owner=user)
        projects = Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user))
        # sprints = Sprint.objects.all()
        success = False
        name_exists = False

        if request.method == 'POST':
            story_name = request.POST["story_name"]
            story_description = request.POST["story_description"]
            story_priority = request.POST["story_priority"]
            story_bussines_value = request.POST["story_bussines_value"]
            # time_cost = request.POST["time_cost"]
            # time_spent = request.POST["time_spent"]
            # asignee = request.POST["asignee"]
            # user_confirmed = request.POST.get('user_confirmed', "") == "on"
            comment = request.POST['comment']
            # story_status = request.POST['story_status']
            project = request.POST['project']
            # sprint = request.POST['sprint'] if request.POST['sprint'] else None

            # if time_cost == '':
            #     time_cost = None

            try:
                Story.objects.get(name=story_name, project_id=int(project))
                name_exists = not name_exists
            except Story.DoesNotExist:
                story = Story(name=story_name,
                            description=story_description,
                            priority=story_priority,
                            businessValue=story_bussines_value,
                            #timeCost=time_cost,
                            # timeSpent=time_spent,
                            # assignedUser_id=asignee,
                            # userConfirmed=user_confirmed,
                            comment=comment,
                            developmentStatus='new',
                            project_id=project,
                            # sprint_id=sprint
                            )
                story.save()
                success = not success

        return render(request,    'new_story.html',
                    context={   'activate_newstory': 'active',
                                # 'users': users,
                                'projects': projects,
                                'success': success,
                                # 'sprints': sprints,
                                'name_exists':name_exists
                                })
    else:
        return HttpResponseRedirect('/login')

def new_project_form(request):
    if request.user.is_authenticated:
        users =  get_user_model().objects.all()
        success = False
        name_exists = False
        dev_and_product_own = False
        if request.method == 'POST':
            project_name =request.POST["project_name"]
            product_owner = request.POST["product_owner"]
            product_owner = User.objects.get(username=product_owner)
            scrum_master = request.POST["scrum_master"]
            scrum_master = User.objects.get(username=scrum_master)
            description = request.POST["description"]
            projects = Project.objects.filter(projectName__iexact=project_name)
            if len(projects) > 0:
                name_exists = True
                
            if name_exists == False:
                project = Project(projectName=project_name, product_owner=product_owner, scrum_master=scrum_master,description=description)
                if request.POST["product_owner"] not in request.POST.getlist("developers"):
                    project.save()
                    for dev_team_member in request.POST.getlist("developers"):
                        user = User.objects.get(username=dev_team_member)
                        dev_team_member = DevTeamMember(userId=user, projectId=project)
                        dev_team_member.save()   
                        success = True
                else:
                    dev_and_product_own = True 

        return render(request,    'new_project.html',
                    context={   'activate_newproject':'active',
                                'users':users,
                                'success': success,
                                'name_exists':name_exists,
                                'dev_and_product_own':dev_and_product_own
                                })
    else:
        return HttpResponseRedirect('/login')

def new_task_form(request):
    if request.user.is_authenticated:
  
        if request.method == 'POST':
            story_id = request.POST["story"]
            story = Story.objects.get(id=story_id)
            timeCost = request.POST["time_cost"]
            description = request.POST["description"]
            assignedUser = request.POST["assignedUser"]
            user = None
            userConfirmed = 'free'
            if assignedUser != "Unassigned":
                user = User.objects.get(username=assignedUser)
                userConfirmed = 'pending'
            task = Task(story=story,  description=description,timeCost=timeCost,assignedUser=user,userConfirmed=userConfirmed)
            task.save()
            return HttpResponseRedirect('/project/story/?id='+story_id)
        else:
            story_id = request.GET.get('story_id')
            story = Story.objects.get(id=story_id)
            project = story.project
            sprint = story.sprint
            dev_team_members = DevTeamMember.objects.filter(projectId=project)
            return render(request, "new_task.html", context={'users':dev_team_members, 'story':story })
    else:
        return HttpResponseRedirect('/login')
        

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

    user = User.objects.get(id=request.user.id)
    print(user)
    lastLogin, sth = LastLogin.objects.get_or_create(user_id=request.user.id)

    lastLogin.lastLoginTime = user.last_login
    lastLogin.save()

    logout(request)

    return HttpResponseRedirect('/login/')  

def new_sprint_form(request):
    if request.user.is_authenticated:
        utc = pytz.UTC

        success = False
        start_overlapping = False
        startBigger = False
        minEndDate = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        minStartDate = datetime.date.today().strftime("%Y-%m-%d")

        user = get_user_model().objects.get(id=request.user.id)
        projects = Project.objects.filter(scrum_master=user)

        if request.method == 'POST':
            project_id = request.POST['project']
            start = request.POST['start']
            start = datetime.datetime.strptime(start, '%Y-%m-%d')
            start = utc.localize(start)
            end = request.POST['end']
            end = datetime.datetime.strptime(end, '%Y-%m-%d')
            end = utc.localize(end)
            speed = request.POST['speed']
            # get all sprints on a project and check end date against starting date
            project = Project.objects.get(id=project_id)
            sprints = Sprint.objects.filter(project=project)
            for sprint in sprints:
                sprintEnd = sprint.end
                if sprintEnd >= start:
                    start_overlapping = True
                    return render(request, 'new_sprint.html', context={'projects': projects,
                                                                    'minStartDate': minStartDate,
                                                                    'minEndDate': minEndDate,
                                                                    'startDateOverlapping': start_overlapping,
                                                                    'startBigger': startBigger,
                                                                    'success': success,
                                                                    'projectField': project_id,
                                                                    'activate_newsprint': 'active',
                                                                    'speedField': speed})
                if start > end:
                    startBigger = True
                    return render(request, 'new_sprint.html', context={'projects': projects,
                                                                    'minStartDate': minStartDate,
                                                                    'minEndDate': minEndDate,
                                                                    'startDateOverlapping': start_overlapping,
                                                                    'startBigger': startBigger,
                                                                    'success': success,
                                                                    'projectField': project_id,
                                                                    'activate_newsprint': 'active',
                                                                    'speedField': speed})


            # add sprint
            sprint = Sprint(project=project,
                            start=start,
                            end=end,
                            expectedSpeed=speed)
            sprint.save()
            success = True

        return render(request, 'new_sprint.html', context={'projects': projects,
                                                        'minStartDate': minStartDate,
                                                        'minEndDate': minEndDate,
                                                        'activate_newsprint': 'active',
                                                        'success': success})
    else:
        return HttpResponseRedirect('/login')



def my_tasks(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)

        
        #for project in projects:
        #    stories = Story.objects.filter(Q(project_id=project))
        #    for story in stories:
        #        tasks = Task.objects.filter(Q(story_id=story))
        #        for task in tasks:
        #            continue

        #data_projects = { project : { story : Task.objects.filter(Q(story_id=story)) for story in Story.objects.filter(Q(project_id=project)) } for project in projects}

        #dobil bi rad storyje ločene na projekt
        #stories = Story.objects.filter(Q(project_id=project))

        #dobil bi rad taske ločene na story
        #tasks = Task.objects.filter(Q(story_id=story))

        #print("OUT: ", list(request.POST.items()), file=sys.stderr)

        #dev = DevTeamMember.objects.filter(userId_id=user)

        #projects =

        #projects_dev = DevTeamMember.objects.projects

        #dodat da si developer

        #projects = Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user))
        #projects = Project.objects.filter(Q(id=dev))
        #projects = Project.objects.filter(id=dev)

        projects = {Project.objects.get(id=devTeamMember.projectId_id) for devTeamMember in DevTeamMember.objects.filter(userId_id=user)}

        return render(request, 'my_tasks.html', context={'projects': projects,
                                                         'activate_mytasks': 'active'})
    else:
        return HttpResponseRedirect('/login')


def update_task_asign(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            task_id = request.POST['task_id']
            userConfirmed = request.POST['userConfirmed']

            #print("OUT: ", userConfirmed, file=sys.stderr)

            task = Task.objects.get(id=int(task_id))
            if userConfirmed == "Accept":
                task.userConfirmed = 'accepted'
                task.assignedUser_id = get_user_model().objects.get(id=request.user.id)
            else:
                task.userConfirmed = 'rejected'
                task.assignedUser_id = None
            task.save()

    return HttpResponse(task_id)




def new_post_form(request):
    utc = pytz.UTC
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        if request.is_ajax and request.method == 'POST':
            description = request.POST['description']
            project_id = request.POST['project']
            project = Project.objects.get(id=project_id)
            time_posted = utc.localize(datetime.datetime.now())
            post = Post(project=project,user=user,time_posted=time_posted,description=description)
            post.save()
            return JsonResponse({"username":user.username,"time_posted":time_posted,"description":description}, status=200, safe=False)
        return JsonResponse({"errorMsg": ""}, status=400)


def user_settings(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id) 
        success = False
        username_exists = False
        email_exists = False
        if request.method == "POST":
            username = request.POST['username']
            firstname = request.POST['first_name']
            lastname = request.POST['last_name']
            email = request.POST['email']
            if user.username != username and User.objects.filter(username=username):
                username_exists = True
                return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email, "username_exists":username_exists})
            elif user.email != email and User.objects.filter(email=email):
                email_exists = True
                return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email, "email_exists":email_exists})
            else:
                user.username = username
                user.first_name = firstname
                user.last_name = lastname
                user.email = email
                user.save()
                success = True
                return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email, "success":success})
        else:
            username = user.username
            firstname = user.first_name
            lastname = user.last_name
            email = user.email
            return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email})
    else:
       return HttpResponseRedirect('/login/') 




def change_password(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password was successfully updated!')
                success = True
                return render(request, 'change_password.html', {'form':form, 'success':success})
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = PasswordChangeForm(request.user)
        return render(request, 'change_password.html', {
            'form': form
        })
    else:
        return HttpResponseRedirect('/login/') 


def delete_task(request, story_id, task_id):
    if request.user.is_authenticated:
        story = Story.objects.get(id=story_id)
        project = story.project
        dev_team_members = project.getDevTeamMembers()
        scrum_master = project.scrum_master
        task = Task.objects.get(id=task_id)
        if (request.user in dev_team_members or request.user == scrum_master) and task.userConfirmed != 'accepted':
            task.delete()
            return JsonResponse({"text":"text"}, status=200, safe=False)
        else:
            if(request.user not in dev_team_members and request.user != scrum_master):
                return JsonResponse({"errorMsg": "User is not dev member or scrum master"}, status=400)
            else:
                return JsonResponse({"errorMsg": "Task is already accepted"}, status=400)
        
    else:
      return HttpResponseRedirect('/login/')  




class TaskUpdateView(BSModalUpdateView):
    model = Task
    template_name = 'update_task.html'
    form_class = TaskModelForm
    success_message = 'Success: Task was updated.'
    success_url = reverse_lazy('index')

    def post(self,request, pk):
        if request.user.is_authenticated:
            task = Task.objects.get(pk=pk)
            story = task.story
            project = story.project
            dev_team_members = project.getDevTeamMembers()
            scrum_master = project.scrum_master
            is_dev_team_member = False
            for dev_team_member in dev_team_members:
                if request.user == dev_team_member.userId:
                    is_dev_team_member = True
            if (is_dev_team_member or request.user == scrum_master) and task.userConfirmed != 'accepted' :
                new_description = request.POST["description"]
                new_timeCost = request.POST["time_cost"]
                new_assignedUser = request.POST["assignedUser"]
                done = request.POST.get('done', "false")
                task.description = new_description
                task.timeCost = new_timeCost
                task.done = done == "on"
                if new_assignedUser != 'None':
                    task.assignedUser = User.objects.get(username=new_assignedUser)
                    task.userConfirmed = 'pending'
                else:
                    task.assignedUser = None
                    task.userConfirmed = 'free'
                task.save()
                return HttpResponseRedirect('/project/story/?id='+str(story.id))
            else:
                HttpResponse("<div class='.invalid'></div>")
        else:
            return HttpResponseRedirect('/login/')

    def get(self,request,pk):
        if request.user.is_authenticated:
            task = Task.objects.get(pk=pk)
            story = task.story
            project = story.project
            dev_team_members = project.getDevTeamMembers()
            scrum_master = project.scrum_master
            return render(request, "update_task.html",context={'task':task,'users':dev_team_members})
        else:
            return HttpResponseRedirect('/login/')

def logTime(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # updating time done on task from stopwatch
            # to be changes on form submision

            today = datetime.date.today()

            taskId = request.POST['id']
            time = request.POST['time']

            task = Task.objects.get(pk=taskId)
            timeSpent = TimeSpent.objects.filter(task=task, date=today)

            if len(timeSpent) == 0:
                timeSpent = TimeSpent(task=task, date=today, time_spent=time)
                timeSpent.save()
            else:
                timeSpent = timeSpent[0]
                timeSpent.time_spent = timeSpent.time_spent + int(time)
                timeSpent.save()

            times = TimeSpent.objects.filter(task=task)

            for time in times:
                remain = int(time.time_spent)
                hours = int(remain / 3600)
                remain -= hours * 3600
                mins = int(remain / 60)
                remain -= mins * 60
                secs = remain

                hours = str(hours)
                if len(hours) < 2:
                    hours = '0' + hours
                mins = str(mins)
                if len(mins) < 2:
                    mins = '0' + mins
                secs = str(secs)
                if len(secs) < 2:
                    secs = '0' + secs

                time.time_spent = hours + ':' + mins + ':' + secs

            return render(request, "log_time.html", context={'task': task, 'times': times})
        else:
            task = Task.objects.get(pk=request.GET.get('id'))
            times = TimeSpent.objects.filter(task=task)

            for time in times:
                remain = int(time.time_spent)
                hours = int(remain / 3600)
                remain -= hours * 3600
                mins = int(remain / 60)
                remain -= mins * 60
                secs = remain

                hours = str(hours)
                if len(hours) < 2:
                    hours = '0' + hours
                mins = str(mins)
                if len(mins) < 2:
                    mins = '0' + mins
                secs = str(secs)
                if len(secs) < 2:
                    secs = '0' + secs

                time.time_spent = hours + ':' + mins + ':' + secs

            return render(request, "log_time.html", context={'task': task, 'times': times})
    else:
        return HttpResponseRedirect('/login/')

