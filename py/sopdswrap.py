import sopdscfg
import sopdstempl
import datetime

def websym(s,attr=False):
    """Replace special web-symbols"""
    result = s
    if attr:
        table = {'"':'\''}
    else:
        table = {'&':'&amp;','<':'&lt;'}
    for k in table.keys():
        result = result.replace(k,table[k])
    return result;

#######################################################################
#
# Базовый класс формирующий вывод
#
class baseWrapper():
    def __init__(self, cfg, template):
        self.cfg=cfg
        self.template=template
        self.response_status='200 Ok'
        self.response_headers=[]
        self.response_body=[]

    def resetParams(self):
        self.response_status='200 Ok'
        self.response_headers=[]
        self.response_body=[]

    def add_response_body(self, string='', encoding='utf8'):
        self.response_body+=[string.encode(encoding)]

    def add_response_binary(self, data):
        self.response_body+=[data]

    def add_response_header(self,list):
        self.response_headers+=list

    def set_response_status(self,status):
        self.response_status=status

    def write_response_headers(self, encoding='utf8'):
        sys.stdout.buffer.write(b'Status: '+self.response_status.encode(encoding)+ b'\n')
        for header in self.response_headers:
            (a,b)=header
            sys.stdout.buffer.write(a.encode(encoding)+b': '+b.encode(encoding) + b'\n')
        sys.stdout.buffer.write(b'\n')

    def write_response(self):
        for element in self.response_body:
            sys.stdout.buffer.write(element + b'\n')

    def header(self, h_id=None, h_title=None, h_subtitle=None, h_time='2014-01-01 00:00:00'):
        self.add_response_header([self.template.response_header])
        self.add_response_body(self.template.document_header%{'id':h_id,'title':h_title,'subtitle':h_subtitle,'updated':h_time,'site_icon':self.cfg.SITE_ICON,'site_author':self.cfg.SITE_AUTOR,'site_url':self.cfg.SITE_URL,'site_email':self.cfg.SITE_EMAIL})

    def footer(self):
        self.add_response_body(self.template.document_footer)

    def main_menu(self,USER,DBINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_mainmenu_std%{'cat_num':DBINFO[2][1],'book_num':DBINFO[0][1],'author_num':DBINFO[1][1],'genre_num':DBINFO[3][1],'series_num':DBINFO[4][1],'alphabet_id':am})
        if self.cfg.NEW_PERIOD!=0:
           self.add_response_body(self.template.document_mainmenu_new%{'new_period':self.cfg.NEW_PERIOD})
        if self.cfg.BOOK_SHELF and USER!=None:
           self.add_response_body(self.template.document_mainmenu_shelf%{'user':USER,'shelf_book_num':DBINFO[5][1]})


    def new_menu(self,NEWINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_newmenu%{'new_period':self.cfg.NEW_PERIOD,'newbook_num':NEWINFO[0][1],'alphabet_id':am})

    def authors_submenu(self,author_id):
        self.add_response_body(self.template.document_authors_submenu%{'author_id':author_id})

    def get_authors(self,tupleAUTHORS):
        authors=""
        authors_link=""
        for (author_id,first_name,last_name) in tupleAUTHORS:
            authors_link+=self.template.agregate_authors_link%{'author_id':author_id,'last_name':websym(last_name,True),'first_name':websym(first_name,True)}
            authors+=self.template.agregate_authors%{'author_id':author_id,'last_name':websym(last_name,True),'first_name':websym(first_name,True)}
#            if len(authors)>0:
#               authors+=', '
#            authors+=last_name+' '+first_name
        return (authors, authors_link)

    def get_genres(self,tupleGENRES):
        genres=""
        genres_link=""
        for (genre_id,section,genre) in tupleGENRES:
            genres_link+=self.template.agregate_genres_link%{'genre_id':genre_id,'genre':websym(genre)}
            genres+=self.template.agregate_genres%{'genre_id':genre_id,'genre':websym(genre)}
#            if len(genres)>0:
#                  genres+=', '
#            genres+=genre
        return (genres, genres_link)

    def get_series(self,tupleSERIES):
        series=""
        series_link=""
        for (ser_id,ser,ser_no) in tupleSERIES:
            series_link+=self.template.agregate_series_link%{'ser_id':ser_id,'ser':websym(ser),'ser_no':ser_no}
            series+=self.template.agregate_series%{'ser_id':ser_id,'ser':websym(ser),'ser_no':ser_no}
#            if len(series)>0:
#                  series+=', '
#            series+=ser
#            if ser_no > 0:
#                  series += ' #' + str(ser_no)
        return (series, series_link)

    def entry_navigation(self,nav_data):
        self.add_response_body(self.template.document_entry_nav_start%nav_data)
        self.add_response_body(self.template.document_entry_nav_title%nav_data)
        self.add_response_body(self.template.document_entry_nav_link%nav_data)
        self.add_response_body(self.template.document_entry_nav_info%nav_data)
        self.add_response_body(self.template.document_entry_nav_finish%nav_data)

    def entry_acq_link_book(self,acq_data):
        data=acq_data.copy()
        if data['e_date']==None:
           data['e_date']=datetime.datetime(2001,9,9,0,0,0)
        self.add_response_body(self.template.document_entry_acq_book_title%data)
        self.add_response_body(self.template.document_entry_acq_book_link_alternate%data)
        data['id']=91
        self.add_response_body(self.template.document_entry_acq_book_link%data)
        data['id']=92
        data['format']=data['format']+'.zip'
        self.add_response_body(self.template.document_entry_acq_book_link%data)
        if acq_data['format'].lower()=='fb2' and self.cfg.FB2TOEPUB:
           data['id']=93
           data['format']='epub'
           self.add_response_body(self.template.document_entry_acq_book_link%data)
        if acq_data['format'].lower()=='fb2' and self.cfg.FB2TOMOBI:
           data['id']=94
           data['format']='mobi'
           self.add_response_body(self.template.document_entry_acq_book_link%data)

    def entry_acq_info_book(self,acq_data):
        self.add_response_body(self.template.document_entry_acq_infobook_start)
        if acq_data['e_title']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_title%acq_data)
        if acq_data['authors']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_authors%acq_data)
        if acq_data['genres']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_genres%acq_data)
        if acq_data['series']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_series%acq_data)
        if acq_data['filename']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_filename%acq_data)
        if acq_data['filesize']>0:
           self.add_response_body(self.template.document_entry_acq_infobook_filesize%acq_data)
        if acq_data['docdate']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_docdate%acq_data)
        if acq_data['annotation']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_annotation%acq_data)
        self.add_response_body(self.template.document_entry_acq_infobook_userdata%acq_data)
        self.add_response_body(self.template.document_entry_acq_infobook_finish)

    def entry_acq_rel_doubles(self,acq_data):
        if acq_data['dcount']>0:
           self.add_response_body(self.template.document_entry_acq_rel_doubles%acq_data)

    def entry_acquisition(self,acq_data):
        self.add_response_body(self.template.document_entry_acq_start%acq_data)
        self.add_response_body(self.template.document_entry_acq_link_start%acq_data)
        self.entry_acq_link_book(acq_data)
        self.add_response_body(self.template.document_entry_acq_link_finish%acq_data)
        self.add_response_body(self.template.document_entry_acq_info_start%acq_data)
        self.add_response_body(self.template.document_entry_acq_info_cover%acq_data)
        self.entry_acq_info_book(acq_data)
        self.add_response_body(self.template.document_entry_acq_rel_start%acq_data)
        self.entry_acq_rel_doubles(acq_data)
        self.add_response_body(self.template.document_entry_acq_rel_authors%acq_data)
        self.add_response_body(self.template.document_entry_acq_rel_genres%acq_data)
        self.add_response_body(self.template.document_entry_acq_rel_finish%acq_data)
        self.add_response_body(self.template.document_entry_acq_info_finish%acq_data)
        self.add_response_body(self.template.document_entry_acq_finish%acq_data)

    def page_control_prev(self, page, link_id):
           self.add_response_body(self.template.document_page_control_prev%{'link_id':link_id,'page':page-1})

    def page_control_next(self, page, link_id):
           self.add_response_body(self.template.document_page_control_next%{'link_id':link_id,'page':page+1})

    def alphabet_menu(self,iid_value,nl):
        self.add_response_body(self.template.document_alphabet_menu%{'iid':iid_value,'nl':nl})

