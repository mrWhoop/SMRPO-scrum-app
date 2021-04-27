import datetime, pytz, time


import json
from django.db.models.functions import Lower
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
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
from .forms import TaskModelForm, StoryModelForm, DocumentationForm, TimeSpentModelForm
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.files import File



import sys

def get_last_login(user):
    last_login_time = user.last_login
    try:
        lastLogin = LastLogin.objects.get(user_id=request.user.id)
        last_login_time = lastLogin.lastLoginTime
    except:
        pass
    return last_login_time

def index(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
        if user.is_staff:
            projects = Project.objects.all()
        else:
            projects_devs_qs = {Project.objects.filter(id=devTeamMember.projectId_id) for devTeamMember in DevTeamMember.objects.filter(userId_id=user)}
            projects_devs = []
            for project_dev in projects_devs_qs:
                projects_devs.append(project_dev[0])
            projects_qs = Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user) )
            projects =[]
            for project in projects_qs:
                if project:
                    projects.append(project)
            projects = list(set(projects_devs) | set(projects))
        return render(request, 'home.html', context={'projects': projects,
                                                     'activate_home':'active',
                                                     'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def project(request):
    if request.user.is_authenticated:
        usr = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(usr)

        project_id = request.GET.get('id')
        project = Project.objects.get(id=project_id)
        
        posts = project.getPosts().order_by('-time_posted')

    

        notProductOwner = True
        isScrumMaster = project.scrum_master_id == request.user.id
        # check product owner
        if project.product_owner_id == request.user.id:
            notProductOwner = False

        stories = Story.objects.filter(project=project).order_by(Lower('developmentStatus').desc())

        today = datetime.date.today()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1))

        # sprints = Sprint.objects.filter(project=project).filter(start__gte=today)

        sprints = Sprint.objects.filter(project=project).filter(Q(start__lte=yesterday) | Q(end__gte=today))

        ended_sprints = Sprint.objects.filter(project=project).filter(end__lte=today)

        completed_storyes = {story for story in Story.objects.all() if Task.objects.filter(story_id=story.id).filter(done=True).count() == Task.objects.filter(story_id=story.id).count()}

        print(completed_storyes)

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
                                               'activate_home': 'active', 'velocityLeft': velocityLeft, 'velocityExceeded': True, 'notProductOwner': notProductOwner, 'isScrumMaster':isScrumMaster,
                                                     'lastLogin': last_login_time})
                    StoryObject.sprint_id = value
                    StoryObject.save()

                if field == 'status' and value != 'None':
                    StoryObject = Story.objects.get(id=int(story_id))
                    StoryObject.developmentStatus = value

                    if value == "rejected":
                        StoryObject.sprint_id = None

                    StoryObject.save()

                if field == 'comment' and value != 'None':
                    StoryObject = Story.objects.get(id=int(story_id))
                    StoryObject.comment = value
                    StoryObject.save()


        return render(request, 'project.html', context={'project': project, 'stories': stories, 'sprints': sprints,
                               'activate_home':'active', 'velocityLeft': velocityLeft, 'velocityExceeded': False, 'notProductOwner': notProductOwner, 'isScrumMaster':isScrumMaster, 'posts':posts, 'ended_sprints': ended_sprints, "completed_storyes":completed_storyes,
                                                     'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def story(request):
    if request.user.is_authenticated:
        usr = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(usr)
        
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
        if sprint == None or datetime.datetime.today().date() > sprint.end:
            sprint_active = False
        
        project = story.project
        product_owner = project.product_owner
        if request.user == product_owner:
            user_is_product_owner = True
        zipped = zip(tasks, times)
        return render(request,'story.html', context={'story': story, 'tasks': tasks, 'sprint_active': sprint_active, 'user_is_product_owner': user_is_product_owner, 'tasks_times': zipped, 'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def new_story_form(request):

    if request.user.is_authenticated:
        user = user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
        projects = Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user))
        success = False
        name_exists = False

        if request.method == 'POST':
            story_name = request.POST["story_name"]
            story_description = request.POST["story_description"]
            story_priority = request.POST["story_priority"]
            story_bussines_value = request.POST["story_bussines_value"]
            comment = request.POST['comment']
            project = request.POST['project']

            try:
                Story.objects.get(name=story_name, project_id=int(project))
                name_exists = not name_exists
            except Story.DoesNotExist:
                story = Story(name=story_name,
                            description=story_description,
                            priority=story_priority,
                            businessValue=story_bussines_value,
                            comment=comment,
                            developmentStatus='new',
                            project_id=project
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
                                , 'lastLogin': last_login_time
                                })
    else:
        return HttpResponseRedirect('/login')

def update_project(request, project_id):
    if request.user.is_authenticated:
        project = Project.objects.get(id=project_id)
        users =  get_user_model().objects.all()
        dev_team_members = project.getDevTeamMembers()
        dev_team_members_users = {get_user_model().objects.get(username=devTeamMember.userId) for devTeamMember in dev_team_members}
        other_users = get_user_model().objects.exclude(username__in=dev_team_members_users)
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
            if len(projects) > 0 and project_name != project.projectName:
                name_exists = True
                
            if name_exists == False:
                project.projectName = project_name
                project.product_owner = product_owner
                project.scrum_master = scrum_master
                project.description = description
                if request.POST["product_owner"] not in request.POST.getlist("developers"):
                    project.save()
                    for dev_team_member in request.POST.getlist("developers"):
                        user = User.objects.get(username=dev_team_member)
                        dev = DevTeamMember.objects.filter(Q(userId=user)&Q(projectId=project)).first()
                        if dev == None:
                            new_dev = DevTeamMember(userId=user, projectId=project)
                            new_dev.save()   
                        else:
                            dev.save()   
                        success = True
                else:
                    dev_and_product_own = True 
                if success == True:
                    return HttpResponseRedirect('/')
        
        return render(request, 'update_project.html',context={'project':project, 'devs':project.getDevTeamMembers(), 'users':users, 'current_product_owner':project.product_owner.username, 'current_scrum_master':project.scrum_master.username, 'other_users':other_users, 'dev_and_product_own':dev_and_product_own, 'success': success,
                                'name_exists':name_exists})
    else:
        return HttpResponseRedirect('/login') 

def new_project_form(request):
    if request.user.is_authenticated:
        users =  get_user_model().objects.all()
        success = False
        name_exists = False
        dev_and_product_own = False
        usr = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(usr)
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
                                'dev_and_product_own':dev_and_product_own,
                                'lastLogin': last_login_time
                                })
    else:
        return HttpResponseRedirect('/login')

def new_task_form(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
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
            return render(request, "new_task.html", context={'users':dev_team_members, 'story':story,'lastLogin': last_login_time })
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
        last_login_time = get_last_login(user)
        projects = Project.objects.filter(scrum_master=user)

        if request.method == 'POST':
            project_id = request.POST['project']
            start = request.POST['start']
            start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
            end = request.POST['end']
            end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
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
                                                                    'speedField': speed,
                                                                    'lastLogin': last_login_time})
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
                                                                    'speedField': speed,
                                                                    'lastLogin': last_login_time})


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
                                                        'success': success,
                                                        'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')



def my_tasks(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
        today = datetime.date.today()
        current_sprint = Sprint.objects.filter(Q(start__lte=today)&Q(end__gte=today)).first()
        projects = {Project.objects.get(id=devTeamMember.projectId_id) for devTeamMember in DevTeamMember.objects.filter(userId_id=user)}

        return render(request, 'my_tasks.html', context={'projects': projects,
                                                         'activate_mytasks': 'active',
                                                         'current_sprint': current_sprint,
                                                         'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def work_log(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
        tasks = Task.objects.filter(assignedUser=user)
        return render(request, 'work_log.html', context={'tasks':tasks,'activate_work_log': 'active','lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')


def update_task_asign(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            task_id = request.POST['task_id']
            userConfirmed = request.POST['userConfirmed']
            task = Task.objects.get(id=int(task_id))
            if userConfirmed == "Accept":
                task.userConfirmed = 'accepted'
                task.assignedUser_id = get_user_model().objects.get(id=request.user.id)
            else:
                task.userConfirmed = 'rejected'
                task.assignedUser_id = None
            task.save()

    return HttpResponse(task_id)

def update_task_done(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            task_id = request.POST['task_id']
            done = request.POST['done']
            task = Task.objects.get(id=int(task_id))
            task.done = done == "true"
            if done == "true":
                task.timeCost = 0.0
            #else:
            #    times_spent = TimeSpent.objects.filter(task_id=int(task.id))
            #    task.timeCost = sum([time_spent.time_spent for time_spent in times_spent])
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
        last_login_time = get_last_login(user)
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
                return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email, "username_exists":username_exists,'lastLogin': last_login_time})
            elif user.email != email and User.objects.filter(email=email):
                email_exists = True
                return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email, "email_exists":email_exists,'lastLogin': last_login_time})
            else:
                user.username = username
                user.first_name = firstname
                user.last_name = lastname
                user.email = email
                user.save()
                success = True
                return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email, "success":success,'lastLogin': last_login_time})
        else:
            username = user.username
            firstname = user.first_name
            lastname = user.last_name
            email = user.email
            return render(request, "user_settings.html",context={"username":username,"first_name":firstname,"last_name":lastname,"email":email,'lastLogin': last_login_time})
    else:
       return HttpResponseRedirect('/login/') 




def change_password(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id) 
        last_login_time = get_last_login(user)
        if request.method == 'POST':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password was successfully updated!')
                success = True
                return render(request, 'change_password.html', {'form':form, 'success':success,'lastLogin': last_login_time})
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = PasswordChangeForm(request.user)
        return render(request, 'change_password.html', {
            'form': form,'lastLogin': last_login_time
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


def delete_story(request, story_id):
    if request.user.is_authenticated:
        story = Story.objects.get(id=story_id)
        project = story.project
        product_owner = project.product_owner
        scrum_master = project.scrum_master
        
        if (request.user == product_owner or request.user == scrum_master) and story.developmentStatus != 'done' and story.sprint == None:
            story.delete()
            return JsonResponse({"text":"text"}, status=200, safe=False)
        else:
            if(request.user != product_owner and request.user != scrum_master):
                return JsonResponse({"errorMsg": "User is not product owner or scrum master"}, status=400)
            else:
                return JsonResponse({"errorMsg": "Story is already part of sprint or done"}, status=400)
        
    else:
      return HttpResponseRedirect('/login/')  



class StoryUpdateView(BSModalUpdateView):
    model = Story
    template_name = 'update_story.html'
    form_class= StoryModelForm
    success_message = 'Succes: Story was updated.'
    success_url = reverse_lazy('index')

    def get(self,request,pk):
        if request.user.is_authenticated:
            story = Story.objects.get(pk=pk)
            project = story.project
            return render(request, "update_story.html",context={'story':story})
        else:
            return HttpResponseRedirect('/login/')
    
    def post(self,request,pk):
        if request.user.is_authenticated:
            story = Story.objects.get(pk=pk)
            project = story.project
            product_owner = project.product_owner
            scrum_master = project.scrum_master
            if (request.user == product_owner or request.user == scrum_master) and story.developmentStatus != 'done' and story.sprint == None:
                new_description = request.POST["description"]
                new_name = request.POST["story_name"]
                new_priority = request.POST["story_priority"]
                new_bussines_value = request.POST["story_bussines_value"]
                new_comment = request.POST["comment"]
                
                stories = Story.objects.filter(name__iexact=new_name)
                name_exists = False
                if len(stories) > 0:
                    name_exists = True

                if new_name != story.name and name_exists == True:
                    
                    
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
                    completed_storyes = {story for story in Story.objects.all() if Task.objects.filter(story_id=story.id).filter(done=True).count() == Task.objects.filter(story_id=story.id).count()}

                    velocityLeft = 0
                    if len(sprints) < 1:
                        sprints = None
                    else:
                        sprints = sprints[0]

                        velocityLeft = sprints.expectedSpeed
                        sprintStories = Story.objects.filter(sprint=sprints)
                        for story in sprintStories:
                            velocityLeft -= story.timeCost

                        name_exists = True
                        next_href = '/project/?id='+str(project.id)
                    return render(request, 'project.html', context={'project': project, 'stories': stories, 'sprints': sprints,
                               'activate_home':'active', 'velocityLeft': velocityLeft, 'velocityExceeded': False, 'notProductOwner': notProductOwner, 'isScrumMaster':isScrumMaster, 'posts':posts, 'ended_sprints': ended_sprints, "completed_storyes":completed_storyes, "name_exists":name_exists, "next_href":next_href})
                else:
                    story.name = new_name
                    story.description = new_description
                    story.priority = new_priority
                    story.businessValue = new_bussines_value
                    story.comment = new_comment
                    story.save()
                    return HttpResponseRedirect('/project/?id='+str(project.id))

            else:
                HttpResponse("<div class='.invalid'></div>")
        else:
            return HttpResponseRedirect('/login/')


class TimeSpentUpdateView(BSModalUpdateView):
    model = TimeSpent
    template_name = 'update_time_spent.html'
    form_class = TimeSpentModelForm
    success_message = 'Success: Task was updated.'
    success_url = reverse_lazy('index')

    def get(self, request,pk):
        if request.user.is_authenticated:
            time_spent = TimeSpent.objects.get(pk=pk)
            task = time_spent.task
            return render(request, 'update_time_spent.html', context={'task':task,'time_spent':round(time_spent.time_spent/3600,2)})
        else: 
            return HttpResponseRedirect('/login/')

    def post(self,request,pk):
        if request.user.is_authenticated:
            time_spent = TimeSpent.objects.get(pk=pk)
            task = time_spent.task
            if task.done == False:
                new_time_spent = request.POST["time_spent"]
                new_time_cost = request.POST["time_cost"]
                task.timeCost = new_time_cost
                task.save()
                time_spent.time_spent = int(float(new_time_spent)*3600)
                time_spent.save()
                return HttpResponseRedirect('/work_log/')
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
        usr = get_user_model().objects.get(id=request.user.id) 
        last_login_time = get_last_login(usr)
        if request.method == 'POST':
            # updating time done on task from stopwatch

            taskId = request.POST['id']
            time = request.POST['time']

            task = Task.objects.get(pk=taskId)
            today = datetime.date.today()
            timeSpent = TimeSpent.objects.filter(task=task, date=today)

            if len(timeSpent) == 0:
                timeSpent = TimeSpent(task=task, date=today, time_spent=time)
                timeSpent.startedWorkingOn = None
                timeSpent.save()
            else:
                timeSpent = timeSpent[0]
                timeSpent.time_spent = timeSpent.time_spent + int(time)
                timeSpent.startedWorkingOn = None
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

            return render(request, "log_time.html", context={'workingOnSth': False, 'task': task, 'times': times, 'workDoneToday': 0, 'time': '00:00:00','lastLogin': last_login_time})
        else:
            # check if there is work being done on some other task
            user = get_user_model().objects.get(id=request.user.id)
            tasks_checkings = Task.objects.filter(assignedUser=user, userConfirmed='accepted')
            for tasks_checking in tasks_checkings:
                time_checkings = TimeSpent.objects.filter(task=tasks_checking)
                for time_checking in time_checkings:
                    if time_checking.startedWorkingOn and not time_checking.task_id == int(request.GET.get('id')):
                        return render(request, "log_time.html", context={'workingOnSth': True, 'workingOnTask': tasks_checking,'lastLogin': last_login_time})

            task = Task.objects.get(pk=request.GET.get('id'))
            times = TimeSpent.objects.filter(task=task)

            timeDF = '00:00:00'
            timeSpentWorking = 0
            today = datetime.date.today()
            workDoneToday = TimeSpent.objects.filter(task=task, date=today)
            if workDoneToday:
                startedWorkingOn = workDoneToday[0].startedWorkingOn
                if startedWorkingOn:
                    timeDifference = datetime.datetime.now(datetime.timezone.utc) - startedWorkingOn
                    timeSpentWorking = timeDifference.total_seconds()

                    remain = int(timeSpentWorking)
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

                    timeDF = hours + ':' + mins + ':' + secs

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

            return render(request, "log_time.html", context={'workingOnSth': False, 'task': task, 'times': times, 'workDoneToday': int(timeSpentWorking), 'time': timeDF,'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login/')

def startWorkingOn(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            task_id = request.POST['task_id']
            task = Task.objects.get(pk=task_id)
            today = datetime.date.today()
            timeSpent = TimeSpent.objects.filter(task=task, date=today)

            if len(timeSpent) == 0:
                timeSpent = TimeSpent(task=task, date=today, time_spent=0)
                timeSpent.startedWorkingOn = datetime.datetime.now(datetime.timezone.utc)
                timeSpent.save()

            elif timeSpent[0].startedWorkingOn is None:
                timeSpent = timeSpent[0]
                timeSpent.startedWorkingOn = datetime.datetime.now(datetime.timezone.utc)
                timeSpent.save()

    return HttpResponse(None)

def sprints(request):
    if request.user.is_authenticated:
        usr = get_user_model().objects.get(id=request.user.id) 
        last_login_time = get_last_login(usr)
        project = Project.objects.get(pk=request.GET.get('id'))
        today = datetime.date.today()
        sprint = Sprint.objects.filter(project_id=request.GET.get('id')).filter(start__gte=today)
        return render(request, "sprints.html", context={'project': project, 'sprints': sprint,'lastLogin': last_login_time})

    else:
        return HttpResponseRedirect('/login/')

def editSprint(request):
    if request.user.is_authenticated:
        utc = pytz.UTC

        success = False
        start_overlapping = False
        startBigger = False
        today = datetime.date.today().strftime("%Y-%m-%d")
        minEndDate = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        minStartDate = datetime.date.today().strftime("%Y-%m-%d")

        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
        projects = Project.objects.filter(scrum_master=user)

        if request.method == 'POST':
            project_id = request.POST['projectId']
            sprint_id = request.POST['sprintId']
            changeSprint = Sprint.objects.get(pk=sprint_id)
            startDate = changeSprint.start
            stopDate = changeSprint.end
            start = request.POST['start']
            start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
            end = request.POST['end']
            end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
            speed = request.POST['speed']
            # get all sprints on a project and check end date against starting date
            project = Project.objects.get(id=project_id)
            sprints = Sprint.objects.filter(project=project)
            for sprint in sprints:
                if sprint.id == changeSprint.id:
                    continue
                else:
                    sprintEnd = sprint.end
                    sprintStart = sprint.start
                    if sprintEnd >= start and sprintStart <= start:
                        start_overlapping = True
                        changeSprint.start = start.strftime("%Y-%m-%d")
                        changeSprint.end = end.strftime("%Y-%m-%d")
                        return render(request, 'edit_sprint.html', context={'projects': projects,
                                                                            'project': project,
                                                                            'minStartDate': minStartDate,
                                                                            'minEndDate': minEndDate,
                                                                            'startDateOverlapping': start_overlapping,
                                                                            'startBigger': startBigger,
                                                                            'sprint': changeSprint,
                                                                            'speedField': changeSprint.expectedSpeed,
                                                                            'success': success,
                                                                            'today': today,
                                                                            'startDate': startDate,
                                                                            'stopDate': stopDate
                                                                            ,'lastLogin': last_login_time
                                                                            })
                    if sprintEnd >= end and sprintStart <= end:
                        end_overlapping = True
                        changeSprint.start = start.strftime("%Y-%m-%d")
                        changeSprint.end = end.strftime("%Y-%m-%d")
                        return render(request, 'edit_sprint.html', context={'projects': projects,
                                                                            'project': project,
                                                                            'minStartDate': minStartDate,
                                                                            'minEndDate': minEndDate,
                                                                            'startDateOverlapping': start_overlapping,
                                                                            'startBigger': startBigger,
                                                                            'sprint': changeSprint,
                                                                            'end_overlapping': end_overlapping,
                                                                            'speedField': changeSprint.expectedSpeed,
                                                                            'success': success,
                                                                            'today': today,
                                                                            'startDate': startDate,
                                                                            'stopDate': stopDate
                                                                            ,'lastLogin': last_login_time
                                                                            })
                    if start > end:
                        startBigger = True
                        changeSprint.start = start.strftime("%Y-%m-%d")
                        changeSprint.end = end.strftime("%Y-%m-%d")
                        return render(request, 'edit_sprint.html', context={'projects': projects,
                                                                            'project': project,
                                                                            'minStartDate': minStartDate,
                                                                            'minEndDate': minEndDate,
                                                                            'startDateOverlapping': start_overlapping,
                                                                            'startBigger': startBigger,
                                                                            'sprint': changeSprint,
                                                                            'speedField': changeSprint.expectedSpeed,
                                                                            'success': success,
                                                                            'today': today,
                                                                            'startDate': startDate,
                                                                            'stopDate': stopDate,
                                                                            'lastLogin': last_login_time
                                                                            })

            # add sprint

            changeSprint.start = start
            changeSprint.end = end
            changeSprint.expectedSpeed = speed
            changeSprint.save()
            success = True

            redirectUrl = "/sprints?id=" + str(project.id)

            return redirect(redirectUrl)

        sprint = Sprint.objects.get(pk=request.GET.get('id'))

        startDate = sprint.start
        stopDate = sprint.end

        sprint.start = sprint.start.strftime("%Y-%m-%d")
        sprint.end = sprint.end.strftime("%Y-%m-%d")

        project = Project.objects.get(pk=sprint.project_id)

        return render(request, 'edit_sprint.html', context={'projects': projects,
                                                            'project': project,
                                                            'minStartDate': minStartDate,
                                                            'minEndDate': minEndDate,
                                                            'sprint': sprint,
                                                            'speedField': sprint.expectedSpeed,
                                                            'success': success,
                                                            'today': today,
                                                            'startDate': startDate,
                                                            'stopDate': stopDate,
                                                            'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def deleteSprint(request):
    if request.user.is_authenticated:
        sprint_id = request.GET.get('id')
        project_id = request.GET.get('projid')
        sprint = Sprint.objects.get(pk=sprint_id)
        sprint.delete()

        redirectUrl = "/sprints?id=" + str(project_id)

        return redirect(redirectUrl)
    else:
        return HttpResponseRedirect('/login')

def documentation(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        last_login_time = get_last_login(user)
        if request.method == 'POST':

            form = DocumentationForm(request.POST)

            if form.is_valid():
                projectId = request.POST['id']
                documentation = form.cleaned_data['documentation']
                project = Project.objects.get(pk=projectId)
                project.documentation = documentation
                project.save()

                form = DocumentationForm(initial={'documentation': project.documentation})
                return render(request, 'documentation.html', context={'form': form, 'project': project,  'lastLogin': last_login_time})

        else:
            project = Project.objects.get(pk=request.GET.get('id'))
            form = DocumentationForm(initial={'documentation': project.documentation})
            return render(request, 'documentation.html', context={'form': form, 'project': project,  'lastLogin': last_login_time})
    else:
        return HttpResponseRedirect('/login')

def download(request):
    if request.user.is_authenticated:
        projectId = request.GET.get('id')
        project = Project.objects.get(pk=projectId)

        filename = project.projectName

        with open(filename, 'w', encoding='utf-8') as f:
            myfile = File(f)
            myfile.write(project.documentation)

        return FileResponse(open(filename, 'rb'))
    else:
        return HttpResponseRedirect('/login')

def upload(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            projectId = request.POST['id']
            uploaded_file = request.FILES['document']

            uploaded_file = uploaded_file.read()
            uploaded_file = uploaded_file.replace(b'\r\r\n', b'')

            project = Project.objects.get(pk=projectId)
            project.documentation = uploaded_file.decode('utf8')
            project.save()

            redirectUrl = "/project/documentation/?id=" + str(projectId)
            return redirect(redirectUrl)

        projectId = request.GET.get('id')
        return render(request, 'upload.html', context={'id': projectId})
    else:
        return HttpResponseRedirect('/login')
