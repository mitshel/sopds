from django.shortcuts import render, render_to_response, redirect, Http404
from django.template import Context, RequestContext
from django.template.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage

from opds_catalog.models import Book, Author, Series, bookshelf
from opds_catalog.settings import SPLITITEMS, MAXITEMS, DOUBLES_HIDE, AUTH, VERSION

from sopds_web_backend.settings import HALF_PAGES_LINKS


def sopds_processor(request):
    args={}
    args['sopds_auth']=AUTH
    args['sopds_version']=VERSION
    user=request.user
    if user.is_authenticated():
        result=[]
        for i,row in enumerate(bookshelf.objects.filter(user=user).order_by('-readtime')):
            book = Book.objects.get(id=row.book_id)
            p = {'id':row.id, 'readtime': row.readtime, 'book_id': row.book_id, 'title': book.title, 'authors':book.authors.values()}       
            result.append(p)    
            if (i>=7): break; 
        args['bookshelf']=result

    return args

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
        
        if (len(searchterms)<3) and (searchtype in ('m', 'b', 'e')):
            args['errormsg'] = 'Too few symbols in search string !';
            return render_to_response('sopds_error.html', args)
        
        if searchtype == 'm':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'a':
            try:
                author_id = int(searchterms)
            except:
                author_id = 0
            books = Book.objects.filter(authors=author_id)      
        # Поиск книг по серии
        elif searchtype == 's':
            try:
                ser_id = int(searchterms)
            except:
                ser_id = 0
            books = Book.objects.filter(series=ser_id)    
        # Поиск книг на книжной полке            
        elif searchtype == 'u':
            if AUTH:
                books = Book.objects.filter(bookshelf__user=request.user)
            else:
                books={}                       
        # Поиск дубликатов для книги            
        elif searchtype == 'd':
            #try:
            book_id = int(searchterms)
            mbook = Book.objects.get(id=book_id)
            books = Book.objects.filter(title__iexact=mbook.title, authors__in=mbook.authors.all()).exclude(id=book_id)
            #except:
            #    books={}                    
        
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
        args['searchobject'] = 'title'     
        
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
        
        if searchtype == 'm':
            series = Series.objects.extra(where=["upper(ser) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'b':
            series = Series.objects.extra(where=["upper(ser) like %s"], params=["%s%%"%searchterms.upper()]) 
        elif searchtype == 'e':
            series = Series.objects.extra(where=["upper(ser)=%s"], params=["%s"%searchterms.upper()])         

        if len(series)>0:
            series = series.order_by('ser')   
            
        # Создаем результирующее множество
        result = []
        for row in series:
            p = {'id':row.id, 'ser':row.ser, 'lang_code': row.lang_code, 'book_count': Book.objects.filter(series=row).count()}
            result.append(p)                     
            
        p = Paginator(result, MAXITEMS)
        try:
            series = p.page(page_num)
        except InvalidPage:
            series = p.page(1)
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
        args['series']=series
        args['page_range']= [ i for i in range(firstpage,lastpage+1)]       
        args['searchobject'] = 'series'
                                              
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
        
        if searchtype == 'm':
            #concat(last_name,' ',first_name)
            authors = Author.objects.extra(where=["upper(last_name) like %s"], params=["%%%s%%"%searchterms.upper()])
        elif searchtype == 'b':
            authors = Author.objects.extra(where=["upper(last_name) like %s"], params=["%s%%"%searchterms.upper()])  
        elif searchtype == 'e':
            authors = Author.objects.extra(where=["upper(last_name)=%s"], params=["%s"%searchterms.upper()])   
            
        if len(authors)>0:
            authors = authors.order_by('last_name','first_name')   
            
        # Создаем результирующее множество
        result = []
        for row in authors:
            p = {'id':row.id, 'last_name':row.last_name, 'first_name': row.first_name, 'lang_code': row.lang_code, 'book_count': Book.objects.filter(authors=row).count()}
            result.append(p)                     
            
        p = Paginator(result, MAXITEMS)
        try:
            authors = p.page(page_num)
        except InvalidPage:
            authors = p.page(1)
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
        args['authors']=authors
        args['page_range']= [ i for i in range(firstpage,lastpage+1)]       
        args['searchobject'] = 'author'
                                    
    return render_to_response('sopds_authors.html', args)

def hello(request):
    args = {}
    return render(request, 'sopds_main.html', args)