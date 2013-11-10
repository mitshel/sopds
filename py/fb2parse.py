#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sopdsparse

  
f=open('../test/25453.fb2','rb')
parser=sopdsparse.fb2parser()
parser.parse(f)
print(parser.author_first.getvalue(), parser.author_last.getvalue(), parser.genre.getvalue(), parser.lang.getvalue(), parser.book_title.getvalue())
f.close()
