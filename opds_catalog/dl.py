# -*- coding: utf-8 -*-

import os
import codecs
import base64
import io
import subprocess

from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_page

from opds_catalog.models import Book, bookshelf
from opds_catalog import settings, utils, opdsdb, fb2parse
import opds_catalog.zipf as zipfile

from book_tools.format import create_bookfile, mime_detector
from book_tools.format.mimetype import Mimetype

from constance import config
from PIL import Image

def getFileName(book):
    if config.SOPDS_TITLE_AS_FILENAME:
        transname = utils.translit(book.title + '.' + book.format)
    else:
        transname = utils.translit(book.filename)

    return utils.to_ascii(transname)


def getFileData(book):
    full_path = os.path.join(config.SOPDS_ROOT_LIB, book.path)
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX и INP файл
        inp_path, zip_name = os.path.split(full_path)
        inpx_path, inp_name = os.path.split(inp_path)
        path, inpx_name = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)

    z = None
    fz = None
    s = None
    fo = None

    if book.cat_type==opdsdb.CAT_NORMAL:
        file_path=os.path.join(full_path, book.filename)
        try:
            fo=codecs.open(file_path, "rb")
            #s = fo.read()
        except FileNotFoundError:
            #s = None
            fo = None

    elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
        try:
            fz=codecs.open(full_path, "rb")
            z = zipfile.ZipFile(fz, 'r', allowZip64=True)
            fo= z.open(book.filename)
            #s=fo.read()
        except FileNotFoundError:
            #s = None
            fo = None

    dio = io.BytesIO()
    dio.write(fo.read())
    dio.seek(0)

    if fo: fo.close()
    if z: z.close()
    if fz: fz.close()

    return dio

def getFileDataZip(book):
    transname = getFileName(book)
    fo = getFileData(book)
    dio = io.BytesIO()
    zo = zipfile.ZipFile(dio, 'w', zipfile.ZIP_DEFLATED)
    zo.writestr(transname, fo.read())
    zo.close()
    dio.seek(0)

    return dio

def getFileDataConv(book, convert_type):

    if book.format != 'fb2':
       return None

    fo = getFileData(book)

    if not fo:
        return None

    transname = getFileName(book)

    (n, e) = os.path.splitext(transname)
    dlfilename = "%s.%s" % (n, convert_type)

    if convert_type == 'epub':
        converter_path = config.SOPDS_FB2TOEPUB
    elif convert_type == 'mobi':
        converter_path = config.SOPDS_FB2TOMOBI
    else:
        fo.close()
        return None

    tmp_fb2_path = os.path.join(config.SOPDS_TEMP_DIR, book.filename)
    tmp_conv_path = os.path.join(config.SOPDS_TEMP_DIR, dlfilename)
    fw = open(tmp_fb2_path,'wb')
    fw.write(fo.read())
    fw.close()
    fo.close()

    popen_args = ("\"%s\" \"%s\" \"%s\"" % (converter_path, tmp_fb2_path, tmp_conv_path))
    proc = subprocess.Popen(popen_args, shell=True, stdout=subprocess.PIPE)
    # У следующий строки 2 функции 1-получение информации по конвертации и 2- ожидание конца конвертации
    # В силу 2й функции ее удаление приведет к ошибке выдачи сконвертированного файла
    out = proc.stdout.readlines()

    if os.path.isfile(tmp_conv_path):
        fo = codecs.open(tmp_conv_path, "rb")
    else:
        return None

    dio = io.BytesIO()
    dio.write(fo.read())
    dio.seek(0)

    fo.close()
    os.remove(tmp_fb2_path)
    os.remove(tmp_conv_path)

    return dio

def getFileDataEpub(book):
    return getFileDataConv(book,'epub')

def getFileDataMobi(book):
    return getFileDataConv(book,'mobi')

def Download(request, book_id, zip_flag):
    """ Загрузка файла книги """
    book = Book.objects.get(id=book_id)

    if config.SOPDS_AUTH and request.user.is_authenticated:
        bookshelf.objects.get_or_create(user=request.user, book=book)

    full_path=os.path.join(config.SOPDS_ROOT_LIB,book.path)
    
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX и INP файл
        inp_path, zip_name = os.path.split(full_path)
        inpx_path, inp_name = os.path.split(inp_path)
        path, inpx_name = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)
        
    if config.SOPDS_TITLE_AS_FILENAME:
        transname=utils.translit(book.title+'.'+book.format)
    else:
        transname=utils.translit(book.filename)
        
    transname = utils.to_ascii(transname)
        
    if zip_flag == '1':
        dlfilename=transname+'.zip'   
        content_type= Mimetype.FB2_ZIP if book.format=='fb2' else Mimetype.ZIP
    else:    
        dlfilename=transname
        content_type = mime_detector.fmt(book.format)

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
        try:
            fo=codecs.open(file_path, "rb")
        except FileNotFoundError:
            raise Http404
        s=fo.read()
    elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
        try:
            fz=codecs.open(full_path, "rb")
        except FileNotFoundError:
            raise Http404
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

# Новая версия (0.42) процедуры извлечения обложек из файлов книг fb2, epub, mobi
@cache_page(config.SOPDS_CACHE_TIME)
def Cover(request, book_id, thumbnail=False):
    """ Загрузка обложки """
    book = Book.objects.get(id=book_id)
    response = HttpResponse()
    full_path = os.path.join(config.SOPDS_ROOT_LIB, book.path)
    if book.cat_type == opdsdb.CAT_INP:
        # Убираем из пути INPX и INP файл
        inp_path, zip_name = os.path.split(full_path)
        inpx_path, inp_name = os.path.split(inp_path)
        path, inpx_name = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)

    try:
        if book.cat_type == opdsdb.CAT_NORMAL:
            file_path = os.path.join(full_path, book.filename)
            fo = codecs.open(file_path, "rb")
            book_data = create_bookfile(fo,book.filename)
            image = book_data.extract_cover_memory()
            #fb2.parse(fo, 0)
            fo.close()
        elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
            fz = codecs.open(full_path, "rb")
            z = zipfile.ZipFile(fz, 'r', allowZip64=True)
            fo = z.open(book.filename)
            book_data = create_bookfile(fo, book.filename)
            image = book_data.extract_cover_memory()
            #fb2.parse(fo, 0)
            fo.close()
            z.close()
            fz.close()
    except:
        book_data = None
        image = None

    if image:
        response["Content-Type"] = 'image/jpeg'
        if thumbnail:
            thumb = Image.open(io.BytesIO(image)).convert('RGB')
            thumb.thumbnail((settings.THUMB_SIZE, settings.THUMB_SIZE), Image.ANTIALIAS)
            tfile = io.BytesIO()
            thumb.save(tfile, 'JPEG')
            image = tfile.getvalue()
        response.write(image)

    if not image:
        if os.path.exists(config.SOPDS_NOCOVER_PATH):
            response["Content-Type"] = 'image/jpeg'
            f = open(config.SOPDS_NOCOVER_PATH, "rb")
            response.write(f.read())
            f.close()
        else:
            raise Http404

    return response

# Старая версия (до 0.41) процедуры извлечения обложек из файлов книг только fb2
def Cover0(request, book_id, thumbnail = False):
    """ Загрузка обложки """
    book = Book.objects.get(id=book_id)
    response = HttpResponse()
    c0=0
    full_path=os.path.join(config.SOPDS_ROOT_LIB,book.path)
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX и INP файл
        inp_path, zip_name = os.path.split(full_path)
        inpx_path, inp_name = os.path.split(inp_path)
        path, inpx_name = os.path.split(inpx_path)
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
                if thumbnail:
                    response["Content-Type"] = 'image/jpeg'
                    thumb = Image.open(io.BytesIO(dstr)).convert('RGB')
                    thumb.thumbnail((settings.THUMB_SIZE, settings.THUMB_SIZE), Image.ANTIALIAS)
                    tfile = io.BytesIO()
                    thumb.save(tfile, 'JPEG')
                    dstr = tfile.getvalue()
                else:
                    response["Content-Type"] = fb2.cover_image.getattr('content-type')
                response.write(dstr)
                c0=1
            except:
                c0=0

    if c0==0:
        if os.path.exists(config.SOPDS_NOCOVER_PATH):
            response["Content-Type"]='image/jpeg'
            f=open(config.SOPDS_NOCOVER_PATH,"rb")
            response.write(f.read())
            f.close()
        else:
            raise Http404

    return response

def Thumbnail(request, book_id):
    return Cover(request, book_id, True)


def ConvertFB2(request, book_id, convert_type):
    """ Выдача файла книги после конвертации в EPUB или mobi """
    book = Book.objects.get(id=book_id)
    
    if book.format!='fb2':
        raise Http404

    if config.SOPDS_AUTH and request.user.is_authenticated:
        bookshelf.objects.get_or_create(user=request.user, book=book)

    full_path=os.path.join(config.SOPDS_ROOT_LIB,book.path)
    if book.cat_type==opdsdb.CAT_INP:
        # Убираем из пути INPX и INP файл
        inp_path, zip_name = os.path.split(full_path)
        inpx_path, inp_name = os.path.split(inp_path)
        path, inpx_name = os.path.split(inpx_path)
        full_path = os.path.join(path,zip_name)
            
    if config.SOPDS_TITLE_AS_FILENAME:
        transname=utils.translit(book.title+'.'+book.format)
    else:
        transname=utils.translit(book.filename)      
        
    transname = utils.to_ascii(transname)
      
    (n,e)=os.path.splitext(transname)
    dlfilename="%s.%s"%(n,convert_type)
    
    if convert_type=='epub':
        converter_path=config.SOPDS_FB2TOEPUB
    elif convert_type=='mobi':
        converter_path=config.SOPDS_FB2TOMOBI
    content_type=mime_detector.fmt(convert_type)

    if book.cat_type==opdsdb.CAT_NORMAL:
        tmp_fb2_path=None
        file_path=os.path.join(full_path, book.filename)
    elif book.cat_type in [opdsdb.CAT_ZIP, opdsdb.CAT_INP]:
        try:
            fz=codecs.open(full_path, "rb")
        except FileNotFoundError:
            raise Http404        
        z = zipfile.ZipFile(fz, 'r', allowZip64=True)
        z.extract(book.filename,config.SOPDS_TEMP_DIR)
        tmp_fb2_path=os.path.join(config.SOPDS_TEMP_DIR,book.filename)
        file_path=tmp_fb2_path        
        
    tmp_conv_path=os.path.join(config.SOPDS_TEMP_DIR,dlfilename)
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