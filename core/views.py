from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Departure

class DepartureForm(forms.ModelForm):
    class Meta:
        model = Departure
        fields = ['title', 'country', 'duration_days', 'departure_date', 'group_size_current', 'group_size_max', 'price_gbp']

@login_required
def dashboard(request):
    departures = Departure.objects.all().order_by('departure_date')
    return render(request, 'core/dashboard.html', {'departures': departures})

@login_required
def tours(request):
    return render(request, 'core/tours.html')

@login_required
def customers(request):
    return render(request, 'core/customers.html')

@login_required
def settings(request):
    return render(request, 'core/settings.html')

@login_required
def departures(request):
    if request.method == 'POST':
        form = DepartureForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('departures')
    else:
        form = DepartureForm()
    all_departures = Departure.objects.all().order_by('departure_date')
    return render(request, 'core/departures.html', {'form': form, 'departures': all_departures})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'core/login.html')

def logout(request):
    auth_logout(request)
    return redirect('login')