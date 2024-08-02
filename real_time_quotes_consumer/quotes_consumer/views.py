# views.py

from django.shortcuts import render

def index(request):
    return render(request, 'quotes_consumer/index.html')
