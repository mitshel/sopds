from random import randint
from itertools import chain

from django.shortcuts import render, render_to_response, redirect, Http404
from django.template.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage
from django.db.models import Count, Min
#from django.contrib.gis.db.models.aggregates import Collect
from django.utils.translation import ugettext as _

from opds_catalog import models
from opds_catalog.models import Book, Author, Series, bookshelf, Counter, Catalog, Genre
from opds_catalog.settings import MAXITEMS, DOUBLES_HIDE, AUTH, VERSION, ALPHABET_MENU, SPLITITEMS
from opds_catalog.models import lang_menu

from sopds_web_backend.settings import HALF_PAGES_LINKS




def sopds_processor(request):
    args={}
    args['sopds_auth']=AUTH
    args['sopds_version']=VERSION
    args['alphabet'] = ALPHABET_MENU
    args['splititems'] = SPLITITEMS
    if ALPHABET_MENU:
        args['lang_menu'] = lang_menu
    
    user=request.user
    if user.is_authenticated():
        result=[]
        for row in bookshelf.objects.filter(user=user).order_by('-readtime')[:8]:
            book = Book.objects.get(id=row.book_id)
            p = {'id':row.id, 'readtime': row.readtime, 'book_id': row.book_id, 'title': book.title, 'authors':book.authors.values()}       
            result.append(p)    
        args['bookshelf']=result
        
        random_id = randint(1,Counter.objects.get_counter(models.counter_allbooks))
        try:
            #random_book = Book.objects.get(id=random_id)
            random_book = Book.objects.all()[random_id-1:random_id][0]
        except Book.DoesNotExist:
            random_book= None
                   
        args['random_book'] = random_book
        stats = { d['name']:d['value'] for d in Counter.obj.all().values() }
        stats['lastscan_date']=Counter.obj.get(name='allbooks').update_time
        args['stats'] = stats
        
    return args

# Create your views here.
def SearchBooksView(request):
    #Read searchtype, searchterms, searchterms0, page from form
    args = {}
    args.update(csrf(request))

    if request.GET:
        searchtype = request.GET.get('searchtype', 'm')
        searchterms = request.GET.get('searchterms', '')
        #searchterms0 = int(request.POST.get('searchterms0', ''))
        page_num = int(request.GET.get('page', '1'))
        
        #if (len(searchterms)<3) and (searchtype in ('m', 'b', 'e')):
        #    args['errormsg'] = 'Too few symbols in search string !';
        #    return render_to_response('sopds_error.html', args)
        
        if searchtype == 'm':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%%%s%%"%searchterms.upper()]).order_by('title','-docdate')
            args['breadcrumbs'] = ['Books','Search by title',searchterms]
            
        if searchtype == 'b':
            books = Book.objects.extra(where=["upper(title) like %s"], params=["%s%%"%searchterms.upper()]).order_by('title','-docdate')
            args['breadcrumbs'] = ['Books','Search by title',searchterms]            
            
        elif searchtype == 'a':
            try:
                author_id = int(searchterms)
                author = Author.objects.get(id=author_id)
                aname = "%s %s"%(author.last_name,author.first_name)
            except:
                author_id = 0
                aname = ""                  
            books = Book.objects.filter(authors=author_id).order_by('title','-docdate')  
            args['breadcrumbs'] = ['Books','Search by Author',aname]    
            
        # Поиск книг по серии
        elif searchtype == 's':
            try:
                ser_id = int(searchterms)
                ser = Series.objects.get(id=ser_id).ser
            except:
                ser_id = 0
                ser = ""
            books = Book.objects.filter(series=ser_id).order_by('title','-docdate')    
            args['breadcrumbs'] = ['Books','Search by Series',ser]
            
        # Поиск книг по жанру
        elif searchtype == 'g':
            try:
                genre_id = int(searchterms)
                section = Genre.objects.get(id=genre_id).section
                subsection = Genre.objects.get(id=genre_id).subsection
                args['breadcrumbs'] = ['Books','Search by Genre',section,subsection]
            except:
                genre_id = 0
                args['breadcrumbs'] = ['Books','Search by Genre']
                
            books = Book.objects.filter(genres=genre_id).order_by('title','-docdate') 
                        
            
        # Поиск книг на книжной полке            
        elif searchtype == 'u':
            if AUTH:
                books = Book.objects.filter(bookshelf__user=request.user).order_by('-bookshelf__readtime')
                args['breadcrumbs'] = ['Books','Bookshelf',request.user.username]
                #books = bookshelf.objects.filter(user=request.user).select_related('book')              
            else:
                books={}        
                args['breadcrumbs'] = ['Books', 'Bookshelf'] 
                
        # Поиск дубликатов для книги            
        elif searchtype == 'd':
            #try:
            book_id = int(searchterms)
            mbook = Book.objects.get(id=book_id)
            books = Book.objects.filter(title__iexact=mbook.title, authors__in=mbook.authors.all()).exclude(id=book_id).order_by('-docdate')
            args['breadcrumbs'] = ['Books','Doubles for book',mbook.title]
            
        elif searchtype == 'i':
            try:
                book_id = int(searchterms)
                btitle = Book.objects.get(id=book_id).title
            except:
                book_id = 0
                btitle = ""
            books = Book.objects.filter(id=book_id)                 
            args['breadcrumbs'] = ['Books',btitle]
            
        if len(books)>0:
            books = books.prefetch_related('authors','genres','series')
        
        # Фильтруем дубликаты
        result = []
        prev_title = ''
        prev_authors_set = set()
        for row in books:
            p = {'doubles':0, 'lang_code': row.lang_code, 'filename': row.filename, 'path': row.path, \
                  'registerdate': row.registerdate, 'id': row.id, 'annotation': row.annotation, \
                  'docdate': row.docdate, 'format': row.format, 'title': row.title, 'filesize': row.filesize//1000}
            p['authors'] = row.authors
            p['genres'] = row.genres
            p['series'] = row.series        
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
        args['current'] = 'search'  

        
    return render(request,'sopds_books.html', args)

def SelectSeriesView(request):
    #Read searchtype, searchterms, searchterms0, page from form
    args = {}
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
        args['current'] = 'search'        
        args['breadcrumbs'] = ['Series','Search',searchterms]
                                              
    return render(request,'sopds_series.html', args)

def SearchAuthorsView(request):
    #Read searchtype, searchterms, searchterms0, page from form    
    args = {}
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
        args['current'] = 'search'       
        args['breadcrumbs'] = ['Authors','Search',searchterms]
                                    
    return render(request,'sopds_authors.html', args)

def CatalogsView(request):   
    args = {}

    if request.GET:
        cat_id = request.GET.get('cat', None)
        page_num = int(request.GET.get('page', '1'))   
    else:
        cat_id = None
        page_num = 1

    if cat_id is not None:
        cat = Catalog.objects.get(id=cat_id)
    else:
        cat = Catalog.objects.get(parent__id=cat_id)
    
    catalogs_list = Catalog.objects.filter(parent=cat).order_by("cat_type","cat_name")
    # prefetch_related on sqlite on items >999 therow error "too many SQL variables"
    #books_list = Book.objects.filter(catalog=cat).prefetch_related('authors','genres','series').order_by("title")
    books_list = Book.objects.filter(catalog=cat).order_by("title")
    union_list = list(chain(catalogs_list,books_list)) 
    
    # Получаем результирующий список
    result = []
    for row in union_list:
        if isinstance(row, Catalog):
            p = {'is_catalog':1, 'title': row.cat_name,'id': row.id, 'cat_type':row.cat_type, 'parent_id':row.parent_id}
        else:
            p = {'is_catalog':0, 'lang_code': row.lang_code, 'filename': row.filename, 'path': row.path, \
                  'registerdate': row.registerdate, 'id': row.id, 'annotation': row.annotation, \
                  'docdate': row.docdate, 'format': row.format, 'title': row.title, 'filesize': row.filesize//1000,
                  'authors':row.authors.values(), 'genres':row.genres.values(), 'series':row.series.values()}         
        result.append(p)
                    
    p = Paginator(result, MAXITEMS)
    try:
        items = p.page(page_num)
    except InvalidPage:
        items = p.page(1)
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
          
    args['items']=items
    args['page_range'] = [ i for i in range(firstpage,lastpage+1)]  
    args['cat_id'] = cat_id
    args['current'] = 'catalog'     
    
    breadcrumbs_list = []
    while (cat.parent):
        breadcrumbs_list.insert(0, cat.cat_name)
        cat = cat.parent
    breadcrumbs_list.insert(0, 'ROOT')    
    breadcrumbs_list.insert(0, 'Catalogs')     
    args['breadcrumbs'] =  breadcrumbs_list  
      
    return render(request,'sopds_catalogs.html', args)  

def BooksView(request):   
    args = {}

    if request.GET:
        lang_code = int(request.GET.get('lang', '0'))  
        chars = request.GET.get('chars', '')
    else:
        lang_code = 0
        chars = ''
        
    length = len(chars)+1
    if lang_code:
        sql="""select %(length)s as l, upper(substring(title,1,%(length)s)) as id, count(*) as cnt 
               from opds_catalog_book 
               where lang_code=%(lang_code)s and upper(title) like '%(chars)s%%'
               group by upper(substring(title,1,%(length)s)) 
               order by id"""%{'length':length, 'lang_code':lang_code, 'chars':chars}
    else:
        sql="""select %(length)s as l, upper(substring(title,1,%(length)s)) as id, count(*) as cnt 
               from opds_catalog_book 
               where upper(title) like '%(chars)s%%'
               group by upper(substring(title,1,%(length)s)) 
               order by id"""%{'length':length,'chars':chars}
      
    items = Book.objects.raw(sql)
          
    args['items']=items
    args['current'] = 'book'      
    args['lang_code'] = lang_code   
    args['breadcrumbs'] =  ['Books','Select',lang_menu[lang_code],chars]
      
    return render(request,'sopds_selectbook.html', args)      

def AuthorsView(request):   
    args = {}

    if request.GET:
        lang_code = int(request.GET.get('lang', '0'))  
        chars = request.GET.get('chars', '')
    else:
        lang_code = 0
        chars = ''
        
    length = len(chars)+1
    if lang_code:
        sql="""select %(length)s as l, upper(substring(last_name,1,%(length)s)) as id, count(*) as cnt 
               from opds_catalog_author 
               where lang_code=%(lang_code)s and upper(last_name) like '%(chars)s%%'
               group by upper(substring(last_name,1,%(length)s)) 
               order by id"""%{'length':length, 'lang_code':lang_code, 'chars':chars}
    else:
        sql="""select %(length)s as l, upper(substring(last_name,1,%(length)s)) as id, count(*) as cnt 
               from opds_catalog_author 
               where upper(last_name) like '%(chars)s%%'
               group by upper(substring(last_name,1,%(length)s)) 
               order by id"""%{'length':length,'chars':chars}
      
    items = Author.objects.raw(sql)
          
    args['items']=items
    args['current'] = 'author'      
    args['lang_code'] = lang_code   
    args['breadcrumbs'] =  ['Authors','Select',lang_menu[lang_code],chars]
      
    return render(request,'sopds_selectauthor.html', args)    

def SeriesView(request):   
    args = {}

    if request.GET:
        lang_code = int(request.GET.get('lang', '0'))  
        chars = request.GET.get('chars', '')
    else:
        lang_code = 0
        chars = ''
        
    length = len(chars)+1
    if lang_code:
        sql="""select %(length)s as l, upper(substring(ser,1,%(length)s)) as id, count(*) as cnt 
               from opds_catalog_series 
               where lang_code=%(lang_code)s and upper(ser) like '%(chars)s%%'
               group by upper(substring(ser,1,%(length)s)) 
               order by id"""%{'length':length, 'lang_code':lang_code, 'chars':chars}
    else:
        sql="""select %(length)s as l, upper(substring(ser,1,%(length)s)) as id, count(*) as cnt 
               from opds_catalog_series 
               where upper(ser) like '%(chars)s%%'
               group by upper(substring(ser,1,%(length)s)) 
               order by id"""%{'length':length,'chars':chars}
      
    items = Series.objects.raw(sql)
          
    args['items']=items
    args['current'] = 'series'      
    args['lang_code'] = lang_code   
    args['breadcrumbs'] =  ['Series','Select',lang_menu[lang_code],chars]
      
    return render(request,'sopds_selectseries.html', args)

def GenresView(request):   
    args = {}

    if request.GET:
        section_id = int(request.GET.get('section', '0'))  
    else:
        section_id = 0
        
    if section_id==0:
        items = Genre.objects.values('section').annotate(section_id=Min('id'), num_book=Count('book')).filter(num_book__gt=0).order_by('section')
        args['breadcrumbs'] =  ['Genres','Select']
    else:
        section = Genre.objects.get(id=section_id).section
        items = Genre.objects.filter(section=section).annotate(num_book=Count('book')).filter(num_book__gt=0).values().order_by('subsection')   
        args['breadcrumbs'] =  ['Genres','Select',section]   
          
    args['items']=items
    args['current'] = 'genre'  
    args['parent_id'] = section_id     
       
    return render(request,'sopds_selectgenres.html', args)

def hello(request):
    args = {}
    args['breadcrumbs'] = ['HOME']
    return render(request, 'sopds_selectbook.html', args)
