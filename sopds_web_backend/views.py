from django.shortcuts import render

# Create your views here.
def hello(request):
    args = {}
    return render(request, 'sopds_main.html', args)