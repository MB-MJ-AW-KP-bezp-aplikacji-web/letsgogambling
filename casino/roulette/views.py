from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse

@login_required(login_url='/login/')
def roulette(request):
    return render(request, "casino/roulette/index.html")
