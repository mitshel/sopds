#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xml.parsers.expat

class fb2tag:
   def __init__(self,tags):
       self.tags=tags
       self.index=-1
       self.size=len(self.tags)
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
   def __init__(self,f):
       self.f=f  
       self.author_first=fb2tag(('description','title-info','author','first-name'))
       self.author_last=fb2tag(('description','title-info','author','last-name'))
       self.genre=fb2tag(('description','title-info','genre'))
       self.lang=fb2tag(('description','title-info','lang'))
       self.book_title=fb2tag(('description','title-info','book-title'))

   def xmldecl(self,version, encoding, standalone):
#       print('xml version ',version,', encoding ',encoding)
       pass

   def start_element(self,name,attrs):
#       print('Start element:', name, attrs)
       self.author_first.tagopen(name)
       self.author_last.tagopen(name)
       self.genre.tagopen(name)
       self.lang.tagopen(name)
       self.book_title.tagopen(name)

   def end_element(self,name):
#       print('End element:', name)
       self.author_first.tagclose(name)
       self.author_last.tagclose(name)
       self.genre.tagclose(name)
       self.lang.tagclose(name)
       self.book_title.tagclose(name)

       if name.lower()=='description':
          raise StopIteration
  
   def char_data(self,data):
#       print('Character data:', repr(data))
       value=repr(data)
       self.author_first.setvalue(value)
       self.author_last.setvalue(value)
       self.genre.setvalue(value)
       self.lang.setvalue(value)
       self.book_title.setvalue(value)


   def parse(self):
       parser = xml.parsers.expat.ParserCreate()
       parser.XmlDeclHandler = self.xmldecl
       parser.StartElementHandler = self.start_element
       parser.EndElementHandler = self.end_element
       parser.CharacterDataHandler = self.char_data 
       try:
         parser.Parse(self.f.read(), True)
       except StopIteration:
         print("Stop Parsing")      
  
f=open('../test/test.fb2','rb')
parser=fb2parser(f)
parser.parse()
print(parser.author_first.getvalue(), parser.author_last.getvalue(), parser.genre.getvalue(), parser.lang.getvalue(), parser.book_title.getvalue())
f.close()
