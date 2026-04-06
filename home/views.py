from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render

from chat.forms import RegisterForm


def index(request):
    return render(request, 'home/index.html', {
        'n8n_url': getattr(settings, 'N8N_URL', ''),
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('chat:list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat:list')
    else:
        form = RegisterForm()
    return render(request, 'home/register.html', {'form': form})
