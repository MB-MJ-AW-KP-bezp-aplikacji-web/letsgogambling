from django.shortcuts import render, HttpResponse

# Create your views here.

def roulette(request):
    return render(request,"casino/roulette/base.html")