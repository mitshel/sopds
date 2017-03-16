import xml.parsers.expat
import traceback
import base64

from book_tools.format.bookfile import BookFile
from book_tools.format.mimetype import Mimetype
from book_tools.format.util import strip_symbols

class fb2tag:
   def __init__(self,tags):
       self.tags=tags
       self.attrs=[]
       self.attrss=[]
       self.index=-1
       self.size=len(self.tags)
       self.values=[]
       self.process_value=False
       self.current_value=''
   
   def reset(self):
       self.index=-1
       self.values=[]
       self.attrs=[]
       self.attrss=[]
       self.process_value=False
       self.current_value=''


   def tagopen(self,tag,attrs=[]):
       result=False
       if (self.index+1)<self.size:
          if self.tags[self.index+1]==tag:
             self.index+=1
       if (self.index+1)==self.size:
          self.attrs=attrs
          self.attrss.append(attrs)
          result=True
       # Возвращаем True если дошли до последнего значения дерева тэга
       return result

   def tagclose(self,tag):
       if self.index>=0:
          if self.tags[self.index]==tag:
             self.index-=1
             if self.process_value:
                self.values.append(self.current_value)
             self.process_value=False

   def setvalue(self,value):
       if (self.index+1)==self.size:
          if self.process_value==False:
             self.current_value=value
             self.process_value=True
          else:
             self.current_value+=value

   def getvalue(self): 
       return self.values

   def gettext(self,divider='\n'):
       result=''
       if len(self.values)>0:
          result=divider.join(self.values)
       return result

   def getattr(self, attr):
       if len(self.attrs)>0:
          val=self.attrs.get(attr)
       else:
          val=None
       return val

   def getattrs(self, attr):
      if len(self.attrss)>0:
         val=[a.get(attr) for a in self.attrss if attr in a]
      else:
         val=[]
      return val

class fb2cover(fb2tag):
   def __init__(self,tags):
       self.iscover=False
       self.cover_name=''
       self._cover_data=[]
       self.isfind=False
       fb2tag.__init__(self,tags)

   def reset(self):
       self.iscover=False
       self.cover_name=''
       self._cover_data=[]
       self.isfind=False
       fb2tag.reset(self)

   def tagopen(self,tag,attrs=[]):
       result=fb2tag.tagopen(self,tag,attrs)
       if result:
          idvalue=self.getattr('id')
          if idvalue!=None:
             idvalue=idvalue.lower()
             if idvalue==self.cover_name:
                self.iscover=True
       return result

   def tagclose(self,tag):
       if self.iscover:
          self.isfind=True
          self.iscover=False
       fb2tag.tagclose(self,tag)

   def setcovername(self,cover_name):
       if cover_name!=None and cover_name!='':
          self.cover_name=cover_name


   def add_data(self,data):
       if self.iscover:
          if data!='\\n':
             self._cover_data.append(data)

   @property
   def cover_data(self):
       return ''.join(self._cover_data)

   @cover_data.setter
   def cover_data(self, value):
       self._cover_data = [value]

class fb2parser:
   def __init__(self, readcover=0):
       self.rc=readcover
       self.author_first=fb2tag(('description','title-info','author','first-name'))
       self.author_last=fb2tag(('description','title-info','author','last-name'))
       self.genre=fb2tag(('description','title-info','genre'))
       self.lang=fb2tag(('description','title-info','lang'))
       self.book_title=fb2tag(('description','title-info','book-title'))
       self.annotation=fb2tag(('description','title-info','annotation','p'))
       self.docdate=fb2tag(('description','document-info','date'))
       self.series=fb2tag(('description','title-info','sequence'))
       if self.rc!=0:
          self.cover_name = fb2tag (('description','coverpage','image'))
          self.cover_image = fb2cover (('fictionbook','binary'));
       self.stoptag='description'
       self.process_description=True
       self.parse_error=0
       self.parse_errormsg=''

   def reset(self):
       self.process_description=True
       self.parse_error=0
       self.author_first.reset()
       self.author_last.reset()
       self.genre.reset()
       self.lang.reset()
       self.book_title.reset()
       self.annotation.reset()
       self.series.reset()
       self.docdate.reset()
       if self.rc!=0:
          self.cover_name.reset()
          self.cover_image.reset()

   def start_element(self,name,attrs):
       name=name.lower()
       if self.process_description:
          self.author_first.tagopen(name)
          self.author_last.tagopen(name)
          self.genre.tagopen(name)
          self.lang.tagopen(name)
          self.book_title.tagopen(name)
          self.annotation.tagopen(name)
          self.docdate.tagopen(name,attrs)
          self.series.tagopen(name,attrs)
          if self.rc!=0:
             if self.cover_name.tagopen(name,attrs):
                cover_name=self.cover_name.getattr('l:href')
                if cover_name=='' or cover_name==None:
                   cover_name=self.cover_name.getattr('xlink:href')
                # Если имя файла не начинается с # то значит данных локально в файле fb2 - нет
                if len(cover_name)>0 and cover_name[0]=='#':
                   cover_name=cover_name.strip('#')
                else:
                   cover_name=None
                self.cover_image.setcovername(cover_name)
       if self.rc!=0:
          self.cover_image.tagopen(name,attrs)

   def end_element(self,name):
       name=name.lower()
       if self.process_description:
          self.author_first.tagclose(name)
          self.author_last.tagclose(name)
          self.genre.tagclose(name)
          self.lang.tagclose(name)
          self.book_title.tagclose(name)
          self.annotation.tagclose(name)
          self.docdate.tagclose(name)
          self.series.tagclose(name)
          if self.rc!=0:
             self.cover_name.tagclose(name)
       if self.rc!=0:
          self.cover_image.tagclose(name)
          if self.cover_image.isfind:
             raise StopIteration

       #Выравниваем количество last_name и first_name
       if name=='author': 
          if len(self.author_last.getvalue())>len(self.author_first.getvalue()):
             self.author_first.values.append(" ") 
          elif len(self.author_last.getvalue())<len(self.author_first.getvalue()):
             self.author_last.values.append(" ")

       if name==self.stoptag:
          if self.rc!=0:
             if self.cover_image.cover_name == '':
                raise StopIteration
             else:
                self.process_description=False
          else:
             raise StopIteration

   def char_data(self,data):
       if self.process_description:
          self.author_first.setvalue(data)
          self.author_last.setvalue(data)
          self.genre.setvalue(data)
          self.lang.setvalue(data)
          self.book_title.setvalue(data)
          self.annotation.setvalue(data)
          self.docdate.setvalue(data)
       if self.rc!=0:
          self.cover_image.add_data(data)

   def parse(self,f,hsize=0):
        self.reset()
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.char_data
        try:
            if hsize==0:
                parser.Parse(f.read(), True)
            else:
                parser.Parse(f.read(hsize), True)
        except StopIteration:
            pass
        except Exception as err:
            self.parse_errormsg=err
            self.parse_error=1

class FB2StructureException(Exception):
    def __init__(self, error):
        Exception.__init__(self, 'fb2 verification failed: %s' % error)
        if isinstance(error, Exception):
            print(traceback.print_exc())

class FB2sax(BookFile):
    def __init__(self, file, original_filename):
        BookFile.__init__(self, file, original_filename, Mimetype.FB2)
        self.fb2parser = fb2parser(0)
        self.file.seek(0, 0)
        self.fb2parser.parse(self.file)
        if self.fb2parser.parse_error != 0:
            raise FB2StructureException('FB2sax parse error (%s)'%self.fb2parser.parse_errormsg)
        self.__detect_title()
        self.__detect_authors()
        self.__detect_tags()
        self.__detect_series_info()
        self.__detect_language()
        self.__detect_docdate()
        self.description = self.__detect_description()

    def extract_cover_memory(self):
        imgfb2parser = fb2parser(1)
        self.file.seek(0, 0)
        imgfb2parser.parse(self.file)
        if len(imgfb2parser.cover_image.cover_data)>0:
            try:
                s=imgfb2parser.cover_image.cover_data
                content=base64.b64decode(s)
                return content
            except :
                return None
        return None

    def __detect_title(self):
        res = ''
        if len(self.fb2parser.book_title.getvalue()) > 0:
            res = self.fb2parser.book_title.getvalue()[0].strip(strip_symbols)
        if len(res) > 0:
            self.__set_title__(res)
        return None

    def __detect_docdate(self):
        res = self.fb2parser.docdate.getattr('value') or ''
        if len(res)==0 and len(self.fb2parser.docdate.getvalue()) > 0:
            res = self.fb2parser.docdate.getvalue()[0].strip();
        if len(res) > 0:
            self.__set_docdate__(res)
        return None

    def __detect_authors(self):
        for idx, author in enumerate(self.fb2parser.author_last.getvalue()):
            last_name = author.strip(strip_symbols)
            first_name = self.fb2parser.author_first.getvalue()[idx].strip(strip_symbols)
            self.__add_author__(' '.join([first_name, last_name]), last_name)
        return None

    def __detect_language(self):
        res = ''
        if len(self.fb2parser.lang.getvalue()) > 0:
            res = self.fb2parser.lang.getvalue()[0].strip(strip_symbols)
        if len(res) > 0:
            self.language_code = res
        return None

    def __detect_tags(self):
        for genre in self.fb2parser.genre.getvalue():
            self.__add_tag__(genre.lower().strip(strip_symbols))

    def __detect_series_info(self):
        if len(self.fb2parser.series.attrss)>0:
            s = self.fb2parser.series.attrss[0]
            ser_name = s.get('name')
            if ser_name:
                title = ser_name.strip(strip_symbols)
                index = s.get('number', '0').strip(strip_symbols)

                self.series_info = {
                    'title': title,
                    'index': index
                }

    def __detect_description(self):
        res = ''
        if len(self.fb2parser.annotation.getvalue()) > 0:
            res = ('\n'.join(self.fb2parser.annotation.getvalue()))
        if len(res) > 0:
            return res
        return None

    def __exit__(self, kind, value, traceback):
        pass
