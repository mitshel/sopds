import os, re
from abc import abstractmethod, ABCMeta

from book_tools.format.util import minify_cover

class BookFile(object):
    __metaclass__ = ABCMeta

    def __init__(self, file, original_filename, mimetype):
        self.file = file
        self.mimetype = mimetype
        self.original_filename = original_filename
        self.title = original_filename
        self.description = None
        self.authors = []
        self.tags = []
        self.series_info = None
        self.language_code = None
        self.issues = []
        self.docdate = ''

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, kind, value, traceback):
        pass

    def extract_cover(self, working_dir):
        cover, minified = self.extract_cover_internal(working_dir)
        if cover and not minified:
            minify_cover(os.path.join(working_dir, cover))
        return cover

    def extract_cover_internal(self, working_dir):
        return (None, False)

    def extract_cover_memory(self):
        return None

    @staticmethod
    def __is_text(text):
        return isinstance(text, str)

    def __set_title__(self, title):
        if title and BookFile.__is_text(title):
            title = title.strip()
            if title:
                self.title = title

    def __set_docdate__(self, docdate):
        if docdate and BookFile.__is_text(docdate):
            docdate = docdate.strip()
            if docdate:
                self.docdate = docdate

    def __add_author__(self, name, sortkey=None):
        if not name or not BookFile.__is_text(name):
            return
        name = BookFile.__normalise_string__(name)
        if not name:
            return
        if sortkey:
            sortkey = sortkey.strip()
        if not sortkey:
            sortkey = name.split()[-1]
        sortkey = BookFile.__normalise_string__(sortkey).lower()
        self.authors.append({'name': name, 'sortkey': sortkey})

    def __add_tag__(self, text):
        if text and BookFile.__is_text(text):
            text = text.strip()
            if text:
                self.tags.append(text)

    @staticmethod
    def __normalise_string__(text):
        if text is None:
            return None
        return re.sub(r'\s+', ' ', text.strip())

    def get_encryption_info(self):
        return {}

    def repair(self, working_dir):
        pass
