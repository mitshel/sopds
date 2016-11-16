# -*- coding: utf-8 -*-

import os
import codecs
import base64
import io
import subprocess

from django.http import HttpResponse, Http404

from opds_catalog.models import Book, bookshelf
from opds_catalog import settings, utils, opdsdb, fb2parse
import opds_catalog.zipf as zipfile

def Download(request, book_id, zip_flag):
    """ Загрузка файла книги """
    book = Book.objects.get(id=book_id)

    if settings.AUTH:
        bookshelf.objects.get_or_create(user=request.user, book=book)

    full_path=os.path.join(settings.ROOT_LIB,book.path)
    
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX файл
        inpx_path, zip_name = os.path.split(full_path)
        path, inpx_file = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)
        
    if settings.TITLE_AS_FILENAME:
        transname=utils.translit(book.title+'.'+book.format)
    else:
        transname=utils.translit(book.filename)
        
    transname = utils.to_ascii(transname)
        
    if zip_flag == 1:
        dlfilename=transname+'.zip'   
        content_type='application/zip' 
    else:    
        dlfilename=transname
        if book.format=="fb2":
            content_type='text/xml'
        elif book.format=="epub":
            content_type='application/epub+zip'
        elif book.format=="mobi":
            content_type='application/x-mobipocket-ebook'
        else:
            content_type='application/octet-stream'       

    response = HttpResponse()
    response["Content-Type"]='%s; name="%s"'%(content_type,dlfilename)
    response["Content-Disposition"] = 'attachment; filename="%s"'%(dlfilename)
    response["Content-Transfer-Encoding"]='binary'

    z = None
    fz = None
    s = None
    book_size = book.filesize
    if book.cat_type==opdsdb.CAT_NORMAL:
        file_path=os.path.join(full_path, book.filename)
        book_size=os.path.getsize(file_path)
        fo=codecs.open(file_path, "rb")
        s=fo.read()
    elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
        fz=codecs.open(full_path, "rb")
        z = zipfile.ZipFile(fz, 'r', allowZip64=True)
        book_size=z.getinfo(book.filename).file_size
        fo= z.open(book.filename)
        s=fo.read()

    if zip_flag=='1':
        dio = io.BytesIO()
        zo = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
        zo.writestr(transname,s)
        zo.close()
        buf = dio.getvalue()
        response["Content-Length"] = str(len(buf))
        response.write(buf)        
    else:
        response["Content-Length"] = str(book_size)
        response.write(s)

    fo.close()
    if z: z.close()
    if fz: fz.close()

    return response

def Cover(request, book_id):
    """ Загрузка обложки """
    book = Book.objects.get(id=book_id)
    response = HttpResponse()
    c0=0
    full_path=os.path.join(settings.ROOT_LIB,book.path)
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX файл
        inpx_path, zip_name = os.path.split(full_path)
        path, inpx_file = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)   
         
    if book.format=='fb2':        
        fb2=fb2parse.fb2parser(1)
        if book.cat_type==opdsdb.CAT_NORMAL:
            file_path=os.path.join(full_path,book.filename)
            fo=codecs.open(file_path, "rb")
            fb2.parse(fo,0)
            fo.close()
        elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
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

def ConvertFB2(request, book_id, convert_type):
    """ Выдача файла книги после конвертации в EPUB или mobi """
    book = Book.objects.get(id=book_id)
    
    if book.format!='fb2':
        raise Http404

    if settings.AUTH:
        bookshelf.objects.get_or_create(user=request.user, book=book)

    full_path=os.path.join(settings.ROOT_LIB,book.path)
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX файл
        inpx_path, zip_name = os.path.split(full_path)
        path, inpx_file = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)  
            
    if settings.TITLE_AS_FILENAME:
        transname=utils.translit(book.title+'.'+book.format)
    else:
        transname=utils.translit(book.filename)      
        
    transname = utils.to_ascii(transname)
      
    (n,e)=os.path.splitext(transname)
    dlfilename="%s.%s"%(n,convert_type)
    
    if convert_type=='epub':
        converter_path=settings.FB2TOEPUB
        content_type='application/epub+zip'
    elif convert_type=='mobi':
        converter_path=settings.FB2TOMOBI
        content_type='application/x-mobipocket-ebook'
    else:
        content_type='application/octet-stream'

    if book.cat_type==opdsdb.CAT_NORMAL:
        tmp_fb2_path=None
        file_path=os.path.join(full_path, book.filename)
    elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
        fz=codecs.open(full_path, "rb")
        z = zipfile.ZipFile(fz, 'r', allowZip64=True)
        z.extract(book.filename,settings.TEMP_DIR)
        tmp_fb2_path=os.path.join(settings.TEMP_DIR,book.filename)
        file_path=tmp_fb2_path        
        
    tmp_conv_path=os.path.join(settings.TEMP_DIR,dlfilename)
    popen_args = ("\"%s\" \"%s\" \"%s\""%(converter_path,file_path,tmp_conv_path))
    proc = subprocess.Popen(popen_args, shell=True, stdout=subprocess.PIPE)
    #proc = subprocess.Popen((converter_path.encode('utf8'),file_path.encode('utf8'),tmp_conv_path.encode('utf8')), shell=True, stdout=subprocess.PIPE)
    out = proc.stdout.readlines()

    if os.path.isfile(tmp_conv_path):
        fo=codecs.open(tmp_conv_path, "rb")
        s=fo.read()
        # HTTP Header
        response = HttpResponse()
        response["Content-Type"]='%s; name="%s"'%(content_type,dlfilename)
        response["Content-Disposition"] = 'attachment; filename="%s"'%(dlfilename)
        response["Content-Transfer-Encoding"]='binary'    
        response["Content-Length"] = str(len(s))
        response.write(s)         
        fo.close()
    else:
        raise Http404

    try: 
        if tmp_fb2_path:
            os.remove(tmp_fb2_path)
    except: 
        pass
    try: 
        os.remove(tmp_conv_path)
    except: 
        pass

    return response