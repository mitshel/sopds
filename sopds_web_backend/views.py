from django.shortcuts import render, render_to_response, redirect, Http404
from django.template import Context, RequestContext
from django.template.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage

from opds_catalog.models import Book
from opds_catalog.settings import SPLITITEMS, MAXITEMS, DOUBLES_HIDE

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
        
        books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()])
        
        if len(books)>0:
            books = books.prefetch_related('authors','genres','series').order_by('title','authors','-docdate')
        
        # Фильтруем дубликаты
        result = []
        prev_title = ''
        prev_authors_set = set()
        for row in books:
            p = {'doubles':0, 'lang_code': row.lang_code, 'filename': row.filename, 'path': row.path, \
                  'registerdate': row.registerdate, 'id': row.id, 'annotation': row.annotation, \
                  'docdate': row.docdate, 'format': row.format, 'title': row.title, 'filesize': row.filesize}
            p['authors'] = row.authors.values()
            p['genres'] = row.genres.values()
            p['series'] = row.series.values()          
            if DOUBLES_HIDE and (searchtype != 'd'):
                title = p['title'] 
                authors_set = {a['id'] for a in p['authors']}         
                if title==prev_title and authors_set==prev_authors_set:
                    result[-1]['doubles']+=1
                else:
                    result.append(p)                   
                prev_title = title
                prev_authors_set = authors_set
            else:
                result.append(p)
                        
        p = Paginator(result, MAXITEMS)
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
        
    return render_to_response('sopds_books.html', args)

def SelectSeriesView(request):
    #Read searchtype, searchterms, searchterms0, page from form
    args = RequestContext(request)
    args.update(csrf(request))

    if request.GET:
        searchtype = request.GET.get('searchtype', 'm')
        searchterms = request.GET.get('searchterms', '')
        #searchterms0 = int(request.POST.get('searchterms0', ''))
        page_num = int(request.GET.get('page', '1'))
            
    return render_to_response('sopds_series.html', args)

def SearchAuthorsViews(request):
    #Read searchtype, searchterms, searchterms0, page from form    
    args = RequestContext(request)
    args.update(csrf(request))

    if request.GET:
        searchtype = request.GET.get('searchtype', 'm')
        searchterms = request.GET.get('searchterms', '')
        #searchterms0 = int(request.POST.get('searchterms0', ''))
        page_num = int(request.GET.get('page', '1'))
            
    return render_to_response('sopds_authors.html', args)

def hello(request):
    args = {}
    return render(request, 'sopds_main.html', args)