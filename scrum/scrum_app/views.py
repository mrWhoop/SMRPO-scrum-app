from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.contrib.auth.forms import  AuthenticationForm

def index(request):

    text = 'Hello World!'

    return render(request, 'home.html', context={'text': text, 'string': 'string', 'activate_home':'active'})

def new_story_form(request):
    return render(request, 'new_story.html', context={'activate_newstory':'active'})

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

