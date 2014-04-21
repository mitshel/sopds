#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sopdsparse
import base64

f=open('105863.fb2','rb')
parser=sopdsparse.fb2parser(True)
parser.parse(f)
print("Errorstr= ",parser.parse_errormsg)
print(parser.author_first.getvalue(), parser.author_last.getvalue(), parser.genre.getvalue(), parser.lang.getvalue(), parser.book_title.getvalue())
print(parser.annotation.getvalue())
i=0
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

