from django.shortcuts import render
from django.http import HttpResponse
from .forms import SubscriberForm
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout


def index(request):

    text = 'Hello World!'

    return render(request, 'home.html', context={'text': text, 'string': 'string', 'activate_home':'active'})

def new_story_form(request):
    return render(request, 'new_story.html', context={'activate_newstory':'active'})

def login_user(request):
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        #if form.is_valid():
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request,user)
            return HttpResponseRedirect('/')
        else:
            return render(request,"login.html", {'form':form})    
    else:
        form = SubscriberForm()
    return render(request, "login.html", {'form':form})

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/login')

