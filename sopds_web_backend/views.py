from django.shortcuts import render, render_to_response, redirect, Http404
from django.template import Context, RequestContext
from django.template.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage

from opds_catalog.models import Book
from opds_catalog.settings import SPLITITEMS

from sopds_web_backend.settings import HALF_PAGES_LINKS


# Create your views here.

def SearchBooksView(request):
    #Read searchtype, searchterms, searchterms0, page from form
    args = RequestContext(request)
    args.update(csrf(request))

    if request.GET:
        searchtype = request.GET.get('searchtype', 'm')
        searchterms = request.GET.get('searchterms', '')
        #searchterms0 = int(request.POST.get('searchterms0', ''))
        page_num = int(request.GET.get('page', '1'))
        
        b = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()])
        p = Paginator(b, SPLITITEMS)
        try:
            books = p.page(page_num)
        except InvalidPage:
            books = p.page(1)
            page_num = 1
            
        firstpage = page_num - HALF_PAGES_LINKS
        lastpage = page_num + HALF_PAGES_LINKS
        if firstpage<1:
            lastpage = lastpage - firstpage + 1
            firstpage = 1
            
        if lastpage>p.num_pages:
            firstpage = firstpage - (lastpage-p.num_pages)
            lastpage = p.num_pages
            if firstpage<1:
                firstpage = 1
              
        args['searchterms']=searchterms;
        args['searchtype']=searchtype;
        args['books']=books
        args['page_range']= [ i for i in range(firstpage,lastpage+1)]
        
 
    return render_to_response('sopds_body.html', args)

def SelectSeriesView(request, searchtype=None, searchterms=None, page=None):
    return

def SearchAuthorsViews(request, searchtype=None, searchterms=None, page=None):
    return

def hello(request):
    args = {}
    return render(request, 'sopds_main.html', args)