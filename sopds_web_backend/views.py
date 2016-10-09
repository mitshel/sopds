from django.shortcuts import render, render_to_response, redirect, Http404
from django.template import Context, RequestContext
from django.template.context_processors import csrf

from opds_catalog.models import Book


# Create your views here.

def SearchBooksView(request):
    #Read searchtype, searchterms, searchterms0, page from form
    args = RequestContext(request)
    args.update(csrf(request))
    if request.POST:
        searchtype = request.POST.get('searchtype', 'm')
        searchterms = request.POST.get('searchterms', '')
        #searchterms0 = int(request.POST.get('searchterms0', ''))
        #page = int(request.POST.get('page', '0'))
        
        books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()])
        
    args['searchterms']=searchterms;
    args['searchtype']=searchtype;
    args['books']=books
       
    return render_to_response('sopds_body.html', args)

def SelectSeriesView(request, searchtype=None, searchterms=None, page=None):
    return

def SearchAuthorsViews(request, searchtype=None, searchterms=None, page=None):
    return

def hello(request):
    args = {}
    return render(request, 'sopds_main.html', args)