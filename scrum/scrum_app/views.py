import datetime, pytz

from django.db.models.functions import Lower
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Sprint, Story, Project, DevTeamMember, Task
from django.contrib.auth.models import User
from django.db.models import Q

def index(request):
    if request.user.is_authenticated:
        user = get_user_model().objects.get(id=request.user.id)
        projects = Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user))

        return render(request, 'home.html', context={'projects': projects,
                                                    'activate_home':'active'})
    else:
        return HttpResponseRedirect('/login')

def project(request):
    if request.user.is_authenticated:
        if request.method == 'POST':

            print("OUT: ", list(request.POST.items()), file=sys.stderr)

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
                    StoryObject.sprint_id = value
                    StoryObject.save()

        project_id = request.GET.get('id')

        project = Project.objects.get(id=project_id)
        stories = Story.objects.filter(project=project).order_by(Lower('developmentStatus').desc())

        today = datetime.date.today()

        sprints = Sprint.objects.filter(project=project).filter(start__gte=today)

        return render(request, 'project.html', context={'project': project, 'stories': stories, 'sprints': sprints, 'activate_home':'active'})
    else:
        return HttpResponseRedirect('/login')

def story(request):
    if request.user.is_authenticated:
        story_id = request.GET.get('id')
        story = Story.objects.get(id=story_id)
        tasks = Task.objects.filter(story=story)
        sprint = story.sprint
        sprint_active = True

        utc = pytz.UTC
        if sprint == None or utc.localize(datetime.datetime.today()) > sprint.end:
            sprint_active = False

        return render(request,'story.html', context={'story':story,'tasks':tasks, 'sprint_active':sprint_active})
    else:
        return HttpResponseRedirect('/login')

def new_story_form(request):

    if request.user.is_authenticated:
        users =  get_user_model().objects.all()
        #print("OUT: ", story, file=sys.stderr)
        projects = Project.objects.all()
        sprints = Sprint.objects.all()
        success = False
        name_exists = False

        if request.method == 'POST':
            story_name = request.POST["story_name"]
            story_description = request.POST["story_description"]
            story_priority = request.POST["story_priority"]
            story_bussines_value = request.POST["story_bussines_value"]
            time_cost = request.POST["time_cost"]
            # time_spent = request.POST["time_spent"]
            # asignee = request.POST["asignee"]
            # user_confirmed = request.POST.get('user_confirmed', "") == "on"
            comment = request.POST['comment']
            story_status = request.POST['story_status']
            project = request.POST['project']
            sprint = request.POST['sprint'] if request.POST['sprint'] else None

            if time_cost == '':
                time_cost = None

            try:
                Story.objects.get(name=story_name, project_id=int(project))
                name_exists = not name_exists
            except Story.DoesNotExist:
                story = Story(name=story_name,
                            description=story_description,
                            priority=story_priority,
                            businessValue=story_bussines_value,
                            timeCost=time_cost,
                            # timeSpent=time_spent,
                            # assignedUser_id=asignee,
                            # userConfirmed=user_confirmed,
                            comment=comment,
                            developmentStatus=story_status,
                            project_id=project,
                            sprint_id=sprint)
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
    else:
        return HttpResponseRedirect('/login')

def new_project_form(request):
    if request.user.is_authenticated:
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
            if assignedUser != "Unassigned":
                user = User.objects.get(username=assignedUser)
            task = Task(story=story,  description=description,timeCost=timeCost,assignedUser=user,userConfirmed=False)
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
    logout(request)
    return HttpResponseRedirect('/login/')  

def new_sprint_form(request):
    if request.user.is_authenticated:
        utc = pytz.UTC

        success = False
        start_overlapping = False
        startBigger = False
        minEndDate = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        minStartDate = datetime.date.today().strftime("%Y-%m-%dT%H:%M:%S")

        projects = projects = Project.objects.all()

        if request.method == 'POST':
            project_id = request.POST['project']
            start = request.POST['start']
            start = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M')
            start = utc.localize(start)
            end = request.POST['end']
            end = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M')
            end = utc.localize(end)
            speed = request.POST['speed']
            # get all sprints on a project and check end date against starting date
            project = Project.objects.get(id=project_id)
            sprints = Sprint.objects.filter(project=project)
            for sprint in sprints:
                sprintEnd = sprint.end
                if sprintEnd > start:
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
        #print("OUT: ", data_projects, file=sys.stderr)

        projects = Project.objects.filter(Q(product_owner=user) | Q(scrum_master=user))

        return render(request, 'my_tasks.html', context={'projects': projects,
                                                         'activate_mytasks': 'active'})
    else:
        return HttpResponseRedirect('/login')













