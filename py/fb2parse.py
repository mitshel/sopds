#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sopdsparse
import base64

  
f=open('book1.fb2','rb')
parser=sopdsparse.fb2parser(1)
parser.parse(f)
print(parser.author_first.getvalue(), parser.author_last.getvalue(), parser.genre.getvalue(), parser.lang.getvalue(), parser.book_title.getvalue())
i=0
#if len(parser.cover_image.getvalue())>0:
#   jpg=open('image.jpg','wb')
#   for str in parser.cover_image.getvalue():
#       sstr=str.strip("' ")
#       if sstr!='\\n':
#          print(i,"'"+sstr+"'")
#          i+=1
#          dstr=base64.b64decode(sstr)
#          jpg.write(dstr)
#   jpg.close()   
print(parser.cover_image.cover_data)
jpg=open('image.jpg','wb')
sstr=parser.cover_image.cover_data.strip("' ")
dstr=base64.b64decode(sstr)
jpg.write(dstr)
jpg.close()
print(parser.cover_image.cover_data)
print(parser.cover_image.cover_name)
print(parser.cover_image.getattr('content-type'))
f.close()

