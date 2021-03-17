from django.shortcuts import render
from django.http import HttpResponse


def index(request):

    text = 'Hello World!'

    return render(request, 'home.html', context={'text': text, 'string': 'string' })
