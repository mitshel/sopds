'''
Created on 14 нояб. 2016 г.

@author: Shelepnev, Dmitry
'''

# -*- coding: utf-8 -*-
import os
import zipfile
#from opds_catalog import settings
from constance import config

sAuthor = 'AUTHOR'
sGenre  = 'GENRE'
sTitle  = 'TITLE'
sSeries = 'SERIES'
sSerNo  = 'SERNO'
sFile   = 'FILE'
sSize   = 'SIZE'
sLibId  = 'LIBID'
sDel    = 'DEL'
sExt    = 'EXT'
sDate   = 'DATE'
sLang   = 'LANG'
sInsNo  = 'INSNO'
sFolder = 'FOLDER'
sLibRate= 'LIBRATE'
sKeyWords='KEYWORDS'


class Inpx:
    def __init__(self, inpx_file, append_callback, inpskip_callback = lambda inpx,inp,size:0):
        self.inpx_file = inpx_file
        self.inpx_catalog = os.path.dirname(inpx_file)
        self.inpx_structure = False
        self.inpx_folders = False
        self.inpx_format = []
        self.inpx_archive = False
        self.inpx_arch_fnames = []
        self.inpx_encoding = 'utf-8'
        self.inpx_separator = b'\x04'
        self.inpx_itemseparator = ':'
        self.append_callback = append_callback
        self.inpskip_callback = inpskip_callback
        self.TEST_ZIP = config.SOPDS_INPX_TEST_ZIP
        self.TEST_FILES = config.SOPDS_INPX_TEST_FILES
        self.error = 0       
        
    def parse(self):
        finpx = zipfile.ZipFile(self.inpx_file, "r")
        filelist = finpx.namelist()
        # здесь читаем формат файлов inp, если есть, если нет, то по умолчанию
        if 'structure.info' in filelist:
            self.inpx_structure = True
            fsds = finpx.open('structure.info')
            fsb = str(fsds.read(),'utf-8')
            self.inpx_format = fsb.split(';')
            fsds.close()
            self.inpx_folders = sFolder in self.inpx_format
        else:
            self.inpx_format = [sAuthor,sGenre,sTitle,sSeries,sSerNo,sFile,sSize,sLibId,sDel,sExt,sDate,sLang]

        # здесь читаем список архивов в коллекции, если указано явно
        # эту информацию надо как-то использовать, чтобы протестировать наличие zip
        #if 'archives.info' in filelist:
        #    self.inpx_archive = True
        #    self.inpx_arch_fnames = finpx.open('archives.info').readlines()

        for inp_file in filelist:
            (inp_name,inp_ext) = os.path.splitext(inp_file)

            # Если файл не INP то пропускаем
            if inp_ext.upper() != '.INP':
                continue

            # Пропускаем разбор INP файла, если его размер не изменился
            if self.inpskip_callback(self.inpx_file, inp_file, finpx.getinfo(inp_file).file_size):
                continue

            finp = finpx.open(inp_file)
            for line in finp:
                meta_list = line.split(self.inpx_separator)
                meta_data = {}

                # Добавляем sFolder если он не определен
                if not self.inpx_folders:
                    meta_data[sFolder] = "%s%s" % (inp_name, '.zip')

                for idx, key in enumerate(self.inpx_format):
                    try:
                        if key in [sAuthor,sGenre,sSeries]:
                            meta_data[key] = meta_list[idx].decode(self.inpx_encoding).split(self.inpx_itemseparator)
                            if '' in  meta_data[key]:
                                meta_data[key].remove('')
                        else:
                            meta_data[key] = meta_list[idx].decode(self.inpx_encoding)
                    except IndexError:
                        meta_data[key] = ''

                # Если книга помечена как удаленная в INP, то пропускаем вызов callback
                if not (meta_data[sDel].strip() in ['','0']):
                    continue

                # Если решили проверять на наличие ZIP файла или книги в ZIP, а самого ZIP файла нет - то пропускаем вызов callback
                zip_file = os.path.join(self.inpx_catalog, meta_data[sFolder])
                if (self.TEST_ZIP or self.TEST_FILES) and not os.path.isfile(zip_file):
                    continue

                # Если нужно выполнить проверку книги в ZIP, а ее там не оказалось, то пропускаем вызов callback
                if self.TEST_FILES:
                    if not "%s.%s"%(meta_data[sFile],meta_data[sExt]) in zipfile.ZipFile(zip_file, "r").namelist():
                        continue

                self.append_callback(self.inpx_file, inp_name, meta_data)

            finp.close()
        finpx.close()
        