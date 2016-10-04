from django.shortcuts import render, render_to_response, redirect, Http404

# Create your views here.

def SearchBooksView(request, searchtype=None, searchterms=None, searchterms0=None, page=None):
    return

def SelectSeriesView(request, searchtype=None, searchterms=None, page=None):
    return

def SearchAuthorsViews(request, searchtype=None, searchterms=None, page=None):
    return

def hello(request):
    args = {}
    return render(request, 'sopds_main.html', args)