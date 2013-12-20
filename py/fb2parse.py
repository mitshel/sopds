#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sopdsparse

  
f=open('book.fb2','rb')
parser=sopdsparse.fb2parser(1)
parser.parse(f)
print(parser.author_first.getvalue(), parser.author_last.getvalue(), parser.genre.getvalue(), parser.lang.getvalue(), parser.book_title.getvalue())
print(parser.book_cover.getvalue())
f.close()
