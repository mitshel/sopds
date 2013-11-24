#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xml.parsers.expat

class fb2tag:
   def __init__(self,tags):
       self.tags=tags
       self.index=-1
       self.size=len(self.tags)
       self.values=[]
   
   def reset(self):
       self.index=-1
       self.values=[]

   def tagopen(self,tag):
       if self.index<self.size:
          if self.tags[self.index+1].lower()==tag.lower():
             self.index+=1

   def tagclose(self,tag):
       if self.index>=0:
          if self.tags[self.index].lower()==tag.lower():
             self.index-=1

   def setvalue(self,value):
       if (self.index+1)==self.size:
          self.values.append(value)

   def getvalue(self): 
       return self.values 


class fb2parser:
   def __init__(self):
       self.author_first=fb2tag(('description','title-info','author','first-name'))
       self.author_last=fb2tag(('description','title-info','author','last-name'))
       self.genre=fb2tag(('description','title-info','genre'))
       self.lang=fb2tag(('description','title-info','lang'))
       self.book_title=fb2tag(('description','title-info','book-title'))
       self.parse_error=0

   def reset(self):
       self.parse_error=0
       self.author_first.reset()
       self.author_last.reset()
       self.genre.reset()
       self.lang.reset()
       self.book_title.reset()

   def xmldecl(self,version, encoding, standalone):
       pass

   def start_element(self,name,attrs):
       self.author_first.tagopen(name)
       self.author_last.tagopen(name)
       self.genre.tagopen(name)
       self.lang.tagopen(name)
       self.book_title.tagopen(name)

   def end_element(self,name):
       self.author_first.tagclose(name)
       self.author_last.tagclose(name)
       self.genre.tagclose(name)
       self.lang.tagclose(name)
       self.book_title.tagclose(name)

       #Выравниваем количество last_name и first_name
       if name.lower()=='author': 
          if len(self.author_last.getvalue())>len(self.author_first.getvalue()):
             self.author_first.values.append(" ") 
          elif len(self.author_last.getvalue())<len(self.author_first.getvalue()):
             self.author_last.values.append(" ")

       if name.lower()=='description':
          raise StopIteration
  
   def char_data(self,data):
       value=repr(data)
       self.author_first.setvalue(value)
       self.author_last.setvalue(value)
       self.genre.setvalue(value)
       self.lang.setvalue(value)
       self.book_title.setvalue(value)

   def parse(self,f,hsize):
       self.reset()
       parser = xml.parsers.expat.ParserCreate()
       parser.XmlDeclHandler = self.xmldecl
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
       except:
         parse_error=1
