'''
Created on 14 нояб. 2016 г.

@author: Shelepnev, Dmitry
'''

# -*- coding: utf-8 -*-
import os
import zipfile

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

class Inpx:
    def __init__(self, inpx_file, append_callback, inpskip_callback = lambda inpx,inp,size:0):
        self.inpx_file = inpx_file
        self.inpx_catalog = os.path.dirname(inpx_file)
        self.inpx_format = [sAuthor,sGenre,sTitle,sSeries,sSerNo,sFile,sSize,sLibId,sDel,sExt,sDate,sLang]
        self.inpx_encoding = 'utf-8'
        self.inpx_separator = b'\x04'
        self.inpx_itemseparator = ':'
        self.append_callback = append_callback
        self.inpskip_callback = inpskip_callback
        self.TEST_ZIP = False
        self.TEST_FILES = False
        self.error = 0       
        
    def parse(self):
        finpx = zipfile.ZipFile(self.inpx_file, "r")
        filelist = finpx.namelist()
        for inp_file in filelist:
            (inp_name,inp_ext) = os.path.splitext(inp_file)
            
            # Если файл не INP то пропускаем
            if inp_ext.upper() != '.INP':
                continue
            
            if self.inpskip_callback(self.inpx_file, inp_name,finpx.getinfo(inp_file).file_size):
                continue

            zip_file_name = os.path.join(self.inpx_catalog,"%s%s"%(inp_name,'.zip'))
            
            # Если будем проверять наличие файлов в ZIP то однократно получаем список файлов в обрабатываемом ZIP 
            if self.TEST_FILES: 
                testzip = zipfile.ZipFile(zip_file_name, "r")
                testzip_namelist = testzip.namelist()
            else:
                testzip_namelist = []
            
            # Если решили проверять на наличие ZIP файла или книги в ZIP, а самого ZIP файла нет - то пропускаем обработку всего ZIP файла
            if (self.TEST_ZIP or self.TEST_FILES) and not os.path.isfile(zip_file_name):
                continue 
            
            finp = finpx.open(inp_file)
            for line in finp:
                meta_list = line.split(self.inpx_separator)
                meta_data = {}
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
                if meta_data[sDel].strip()!='':
                    continue          
                
                # Если нужно выполнить проверку книги в ZIP, а ее там не оказалось, то пропускаем вызов callback            
                if self.TEST_FILES:      
                    if not "%s.%s"(meta_data[sFile],meta_data[sExt]) in testzip_namelist:
                        continue 
                            
                self.append_callback(self.inpx_file, inp_name, meta_data)              
 
            finp.close()
        finpx.close()
        