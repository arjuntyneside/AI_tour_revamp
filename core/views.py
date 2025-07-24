from django.shortcuts import render

def dashboard(request):
    return render(request, 'core/dashboard.html')

def tours(request):
    return render(request, 'core/tours.html')