#import magic
import os
import zipfile
from xml import sax

from book_tools.format.mimetype import Mimetype

from book_tools.format.util import list_zip_file_infos
from book_tools.format.epub import EPub
from book_tools.format.fb2 import FB2, FB2Zip
from book_tools.format.other import Dummy
#from fbreader.format.pdf import PDF
#from fbreader.format.msword import MSWord
from book_tools.format.mobi import Mobipocket
#from fbreader.format.rtf import RTF
#from fbreader.format.djvu import DjVu
#from fbreader.format.dummy import Dummy

#__detector = magic.open(magic.MAGIC_MIME_TYPE)
#__detector.load()

class __detector:
    @staticmethod
    def file(filename):
        (n, e) = os.path.splitext(filename)
        if e.lower() == '.xml':
            return Mimetype.XML
        if e.lower() == '.fb2':
            return Mimetype.FB2
        elif e.lower()=='.epub' or e.lower()=='.zip':
            return Mimetype.ZIP
        elif e.lower()=='.pdf':
            return Mimetype.PDF
        elif e.lower()=='.doc' or e.lower()=='.docx':
            return Mimetype.MSWORD
        elif e.lower()=='.djvu':
            return Mimetype.DJVU
        elif e.lower()=='.txt':
            return Mimetype.TEXT
        elif e.lower()=='.rtf':
            return Mimetype.RTF
        else:
            return Mimetype.OCTET_STREAM

def detect_mime(file):
    FB2_ROOT = 'FictionBook'
    mime = __detector.file(file.name)

    try:
        if mime == Mimetype.XML or mime == Mimetype.FB2:
            if FB2_ROOT == __xml_root_tag(file):
                return Mimetype.FB2
        elif mime == Mimetype.ZIP:
            with zipfile.ZipFile(file) as zip_file:
                if not zip_file.testzip():
                    infolist = list_zip_file_infos(zip_file)
                    if len(infolist) == 1:
                        if FB2_ROOT == __xml_root_tag(zip_file.open(infolist[0])):
                            return Mimetype.FB2_ZIP
                    try:
                        with zip_file.open('mimetype') as mimetype_file:
                            if mimetype_file.read(30).decode().rstrip('\n\r') == Mimetype.EPUB:
                                return Mimetype.EPUB
                    except Exception as e:
                        pass
        elif mime == Mimetype.OCTET_STREAM:
            mobiflag =  file.read(68)
            mobiflag = mobiflag[60:]
            if mobiflag.decode() == 'BOOKMOBI':
                return Mimetype.MOBI
    except:
        pass

    return mime

def create_bookfile(file, original_filename):
    if isinstance(file, str):
        file = open(file, 'rb')
    mimetype = detect_mime(file)
    if mimetype == Mimetype.EPUB:
        return EPub(file, original_filename)
    elif mimetype == Mimetype.FB2:
        return FB2(file, original_filename)
    elif mimetype == Mimetype.FB2_ZIP:
        return FB2Zip(file, original_filename)
    elif mimetype == Mimetype.MOBI:
        return Mobipocket(file, original_filename)
    elif mimetype in [Mimetype.TEXT, Mimetype.PDF, Mimetype.MSWORD, Mimetype.RTF, Mimetype.DJVU]:
       return Dummy(file, original_filename, mimetype)
    else:
        raise Exception('File type \'%s\' is not supported, sorry' % mimetype)

def __xml_root_tag(file):
    class XMLRootFound(Exception):
        def __init__(self, name):
            self.name = name

    class RootTagFinder(sax.handler.ContentHandler):
        def startElement(self, name, attributes):
            raise XMLRootFound(name)

    try:
        sax.parse(file, RootTagFinder())
    except XMLRootFound as e:
        return e.name
    return None
