# -*- coding: utf-8 -*-

import os
import codecs
import base64
import io

from django.http import HttpResponse, Http404

from opds_catalog.models import Book, bookshelf
from opds_catalog import settings, utils, opdsdb, fb2parse
import opds_catalog.zipf as zipfile

def Download(request, book_id, zip = 0):
    """ Загрузка файла книги """
    book = Book.objects.get(id=book_id)
    # TODO: Добавить книгу на книжную полку
    if settings.AUTH:
        bookshelf.objects.get_or_create(user=request.user, book=book)

    full_path=os.path.join(settings.ROOT_LIB,book.path)
    if settings.TITLE_AS_FILENAME:
        transname=utils.translit(book.title+'.'+book.format)
    else:
        transname=utils.translit(book.filename)

    if book.format=="fb2":
        content_type='text/xml'
    elif book.format=="epub":
        content_type='application/epub+zip'
    elif book.format=="mobi":
        content_type='application/x-mobipocket-ebook'
    else:
        content_type='application/octet-stream'

    response = HttpResponse()
    response["Content-Type"]='%s; name="%s"'%(content_type,transname)
    response["Content-Disposition"] = 'attachment; filename="%s"'%(transname)
    response["Content-Transfer-Encoding"]='binary'

    z = None
    fz = None
    s = None
    book_size = book.filesize
    if book.cat_type==opdsdb.CAT_NORMAL:
       file_path=os.path.join(full_path,book.filename)
       book_size=os.path.getsize(file_path)
       response["Content-Length"] = str(book_size)
       fo=codecs.open(file_path, "rb")
       s=fo.read()
       response.write(s)
       fo.close()
    elif book.cat_type==opdsdb.CAT_ZIP:
       fz=codecs.open(full_path, "rb")
       z = zipfile.ZipFile(fz, 'r', allowZip64=True)
       book_size=z.getinfo(book.filename).file_size
       fo= z.open(book.filename)
       s=fo.read()

    if not zip:
        response["Content-Length"] = str(book_size)
        response.write(s)
    else:
       dio = io.BytesIO()
       zo = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
       zo.writestr(transname,s)
       zo.close()

       buf = dio.getvalue()
       response["Content-Length"] = str(len(buf))
       response.write(buf)

    fo.close()
    if z: z.close()
    if fz: fz.close()

    return response


def Cover(request, book_id):
    """ Загрузка обложки """
    #(book_name,book_path,reg_date,format,title,annotation,docdate,cat_type,cover,cover_type,fsize)=self.opdsdb.getbook(self.slice_value)
    book = Book.objects.get(id=book_id)
    response = HttpResponse()
    c0=0
    if book.format=='fb2':
       full_path=os.path.join(settings.ROOT_LIB,book.path)
       fb2=fb2parse.fb2parser(1)
       if book.cat_type==opdsdb.CAT_NORMAL:
          file_path=os.path.join(full_path,book.filename)
          fo=codecs.open(file_path, "rb")
          fb2.parse(fo,0)
          fo.close()
       elif book.cat_type==opdsdb.CAT_ZIP:
          fz=codecs.open(full_path, "rb")
          z = zipfile.ZipFile(fz, 'r', allowZip64=True)
          fo = z.open(book.filename)
          fb2.parse(fo,0)
          fo.close()
          z.close()
          fz.close()

       if len(fb2.cover_image.cover_data)>0:
          try:
            s=fb2.cover_image.cover_data
            dstr=base64.b64decode(s)
            response["Content-Type"]=fb2.cover_image.getattr('content-type')
            response.write(dstr)
            c0=1
          except:
            c0=0

    if c0==0:
       if os.path.exists(settings.NOCOVER_PATH):
          response["Content-Type"]='image/jpeg'
          f=open(settings.NOCOVER_PATH,"rb")
          response.write(f.read())
          f.close()
       else:
           raise Http404

    return response
