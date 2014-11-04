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

def dictmerge(a,b={},c={}):
    data=a.copy()
    data.update(b)
    data.update(c)
    return data

#######################################################################
#
# Базовый класс формирующий вывод
#
class baseWrapper():
    def __init__(self, cfg, template, site_data):
        self.cfg=cfg
        self.site_data=site_data
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

    def document_header(self,page_data):
        self.add_response_header([self.template.response_header])
        self.add_response_body(self.template.document_header%dictmerge(self.site_data, page_data, {'style':self.template.document_style}))

    def document_footer(self,page_data):
        self.add_response_body(self.template.document_footer%dictmerge(self.site_data,page_data))

    def page_top(self, page_data):
        data=dictmerge(self.site_data,page_data)
        self.add_response_body(self.template.page_top_start%data)
        self.add_response_body(self.template.page_top_linkstart%data)
        self.add_response_body(self.template.page_top_linkself%data)
        self.add_response_body(self.template.page_top_linksearch%data)
        self.add_response_body(self.template.page_top_finish%data)

    def page_bottom(self, page_data):
        data=dictmerge(self.site_data,page_data)
        self.add_response_body(self.template.page_bottom_start%data)
        self.add_response_body(self.template.page_bottom_info%data)
        self.add_response_body(self.template.page_bottom_finish%data)

    def page_title(self, page_data):
        data=dictmerge(self.site_data,page_data)
        self.add_response_body(self.template.page_title_start%data)
        self.add_response_body(self.template.page_title_info%data)
        self.add_response_body(self.template.page_title_finish%data)


#    def  header(self, page_data):
#        self.add_response_header([self.template.response_header])
#        self.add_response_body(self.template.document_page_header%dictmerge(self.site_data, page_data, {'style':self.template.document_page_header_style}))

#    def footer(self, page_data):
#        self.add_response_body(self.template.document_page_footer%dictmerge(self.site_data,page_data))

    def main_menu(self,USER,DBINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_mainmenu_std%dictmerge(self.site_data,{'cat_num':DBINFO[2][1],'book_num':DBINFO[0][1],'author_num':DBINFO[1][1],'genre_num':DBINFO[3][1],'series_num':DBINFO[4][1],'alphabet_id':am}))
        if self.cfg.NEW_PERIOD!=0:
           self.add_response_body(self.template.document_mainmenu_new%dictmerge(self.site_data,{'new_period':self.cfg.NEW_PERIOD}))
        if self.cfg.BOOK_SHELF and USER!=None:
           self.add_response_body(self.template.document_mainmenu_shelf%dictmerge(self.site_data,{'user':USER,'shelf_book_num':DBINFO[5][1]}))


    def new_menu(self,NEWINFO):
        if self.cfg.ALPHA: am='30'
        else: am=''
        self.add_response_body(self.template.document_newmenu%dictmerge(self.site_data,{'new_period':self.cfg.NEW_PERIOD,'newbook_num':NEWINFO[0][1],'alphabet_id':am}))

    def authors_submenu(self,author_id):
        self.add_response_body(self.template.document_authors_submenu%dictmerge(self.site_data,{'author_id':author_id}))

    def get_authors(self,tupleAUTHORS):
        authors=""
        authors_link=""
        for (author_id,first_name,last_name) in tupleAUTHORS:
            authors_link+=self.template.agregate_authors_link%dictmerge(self.site_data,{'author_id':author_id,'last_name':websym(last_name,True),'first_name':websym(first_name,True)})
            authors+=self.template.agregate_authors%dictmerge(self.site_data,{'author_id':author_id,'last_name':websym(last_name,True),'first_name':websym(first_name,True)})
        return (authors, authors_link)

    def get_genres(self,tupleGENRES):
        genres=""
        genres_link=""
        for (genre_id,section,genre) in tupleGENRES:
            genres_link+=self.template.agregate_genres_link%dictmerge(self.site_data,{'genre_id':genre_id,'genre':websym(genre)})
            genres+=self.template.agregate_genres%dictmerge(self.site_data,{'genre_id':genre_id,'genre':websym(genre)})
        return (genres, genres_link)

    def get_series(self,tupleSERIES):
        series=""
        series_link=""
        for (ser_id,ser,ser_no) in tupleSERIES:
            series_link+=self.template.agregate_series_link%dictmerge(self.site_data,{'ser_id':ser_id,'ser':websym(ser),'ser_no':ser_no})
            series+=self.template.agregate_series%dictmerge(self.site_data,{'ser_id':ser_id,'ser':websym(ser),'ser_no':ser_no})
        return (series, series_link)

    def entry_navigation(self,nav_data):
        data=dictmerge(self.site_data,nav_data)
        self.add_response_body(self.template.document_entry_nav_start%data)
        self.add_response_body(self.template.document_entry_nav_title%data)
        self.add_response_body(self.template.document_entry_nav_link%data)
        self.add_response_body(self.template.document_entry_nav_info%data)
        self.add_response_body(self.template.document_entry_nav_finish%data)

    def entry_acq_link_book(self,acq_data):
        data=dictmerge(self.site_data,acq_data)
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
        data=dictmerge(self.site_data,acq_data)
        self.add_response_body(self.template.document_entry_acq_infobook_start%data)
        if acq_data['e_title']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_title%data)
        if acq_data['authors']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_authors%data)
        if acq_data['genres']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_genres%data)
        if acq_data['series']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_series%data)
        if acq_data['filename']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_filename%data)
        if acq_data['filesize']>0:
           self.add_response_body(self.template.document_entry_acq_infobook_filesize%data)
        if acq_data['docdate']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_docdate%data)
        if acq_data['annotation']!='':
           self.add_response_body(self.template.document_entry_acq_infobook_annotation%data)
        self.add_response_body(self.template.document_entry_acq_infobook_userdata%data)
        self.add_response_body(self.template.document_entry_acq_infobook_finish%data)

    def entry_acq_rel_doubles(self,acq_data):
        data=dictmerge(self.site_data,acq_data)
        if data['dcount']>0:
           self.add_response_body(self.template.document_entry_acq_rel_doubles%acq_data)

    def entry_acquisition(self,acq_data):
        data=dictmerge(self.site_data,acq_data)
        self.add_response_body(self.template.document_entry_acq_start%data)
        self.add_response_body(self.template.document_entry_acq_link_start%data)
        self.entry_acq_link_book(data)
        self.add_response_body(self.template.document_entry_acq_link_finish%data)
        self.add_response_body(self.template.document_entry_acq_info_start%data)
        self.add_response_body(self.template.document_entry_acq_info_cover%data)
        self.entry_acq_info_book(data)
        self.add_response_body(self.template.document_entry_acq_rel_start%data)
        self.entry_acq_rel_doubles(data)
        self.add_response_body(self.template.document_entry_acq_rel_authors%data)
        self.add_response_body(self.template.document_entry_acq_rel_genres%data)
        self.add_response_body(self.template.document_entry_acq_rel_finish%data)
        self.add_response_body(self.template.document_entry_acq_info_finish%data)
        self.add_response_body(self.template.document_entry_acq_finish%data)

    def page_control(self, page_data):
        self.add_response_body(self.template.document_page_control_start%dictmerge(self.site_data,page_data))
        if page_data['page_prev']>=0:
           self.add_response_body(self.template.document_page_control_prev%dictmerge(self.site_data,page_data))
        if page_data['page_next']>=0:
           self.add_response_body(self.template.document_page_control_next%dictmerge(self.site_data,page_data))
        self.add_response_body(self.template.document_page_control_finish%dictmerge(self.site_data,page_data))

    def alphabet_menu(self,iid_value,nl):
        self.add_response_body(self.template.document_alphabet_menu%dictmerge(self.site_data,{'iid':iid_value,'nl':nl}))

    def opensearch(self):
        self.add_response_header([self.template.response_header])
        self.add_response_body(self.template.opensearch%self.site_data)

#    def opensearch_links(self, page_data):
#        self.add_response_body(self.template.opensearch_links%dictmerge(self.site_data,page_data))

    def opensearch_forms(self, page_data):
        self.add_response_body(self.template.opensearch_forms%dictmerge(self.site_data,page_data))


