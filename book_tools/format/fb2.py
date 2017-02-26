import base64, os, traceback, zipfile
from lxml import etree
from abc import abstractmethod

from book_tools.format.bookfile import BookFile
from book_tools.format.mimetype import Mimetype
from book_tools.format.util import list_zip_file_infos

class FB2StructureException(Exception):
    def __init__(self, error):
        Exception.__init__(self, 'fb2 verification failed: %s' % error)
        if isinstance(error, Exception):
            print(traceback.print_exc())

class Namespace(object):
    FICTION_BOOK = 'http://www.gribuser.ru/xml/fictionbook/2.0'
    XLINK = 'http://www.w3.org/1999/xlink'

class FB2Base(BookFile):
    def __init__(self, file, original_filename, mimetype):
        BookFile.__init__(self, file, original_filename, mimetype)
        self.__namespaces = {'fb': Namespace.FICTION_BOOK, 'xlink': Namespace.XLINK}
        try:
            tree = self.__create_tree__()
            self.__detect_title(tree)
            self.__detect_authors(tree)
            self.__detect_tags(tree)
            self.__detect_series_info(tree)
            self.__detect_language(tree)
            self.__detect_docdate(tree)
            description = self.__detect_description(tree)
            if description:
                self.description = description.strip()
        except FB2StructureException as error:
            raise error
        except Exception as error:
            raise FB2StructureException(error)

    @abstractmethod
    def __create_tree__(self):
        return None

    def extract_cover_internal(self, working_dir):
        try:
            tree = self.__create_tree__()
            res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:coverpage/fb:image', namespaces=self.__namespaces)
            cover_id = res[0].get('{' + Namespace.XLINK + '}href')[1:]
            res = tree.xpath('//fb:binary[@id="%s"]' % cover_id, namespaces=self.__namespaces)
            content = base64.b64decode(res[0].text)
            with open(os.path.join(working_dir, 'cover.jpeg'), 'wb') as cover_file:
                cover_file.write(content)
            return ('cover.jpeg', False)
        except:
            return (None, False)

    def extract_cover_memory(self):
        try:
            tree = self.__create_tree__()
            res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:coverpage/fb:image', namespaces=self.__namespaces)
            cover_id = res[0].get('{' + Namespace.XLINK + '}href')[1:]
            res = tree.xpath('//fb:binary[@id="%s"]' % cover_id, namespaces=self.__namespaces)
            content = base64.b64decode(res[0].text)
            return content
        except Exception as err:
            print(err)
            return None

    def __detect_title(self, tree):
        res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:book-title', namespaces=self.__namespaces)
        if len(res) == 0:
            res = tree.xpath('/FictionBook/description/title-info/book-title')
        if len(res) > 0:
            self.__set_title__(res[0].text)

        return None

    def __detect_docdate(self, tree):
        is_attrib = 1
        res = tree.xpath('/fb:FictionBook/fb:description/fb:document-info/fb:date/@value', namespaces=self.__namespaces)
        if len(res) == 0:
            res = tree.xpath('/FictionBook/description/document-info/date/@value')
        if len(res) == 0:
            is_attrib = 0
            res = tree.xpath('/fb:FictionBook/fb:description/fb:document-info/fb:date', namespaces=self.__namespaces)
        if len(res) == 0:
            is_attrib = 0
            res = tree.xpath('/FictionBook/description/document-info/date')
        if len(res) > 0:
            self.__set_docdate__(res[0] if is_attrib else res[0].text)

        return None

    def __detect_authors(self, tree):
        use_namespaces = True

        def subnode_text(node, name):
            if use_namespaces:
                subnode = node.find('fb:' + name, namespaces=self.__namespaces)
            else:
                subnode = node.find(name)
            text = subnode.text if subnode is not None else ''
            return text or ''

        def add_author_from_node(node):
            first_name = subnode_text(node, 'first-name')
            middle_name = subnode_text(node, 'middle-name')
            last_name = subnode_text(node, 'last-name')
            self.__add_author__(' '.join([first_name, middle_name, last_name]), last_name)

        res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:author', namespaces=self.__namespaces)
        if len(res) == 0:
            use_namespaces = False
            res = tree.xpath('/FictionBook/description/title-info/author')

        for node in res:
            add_author_from_node(node)

    def __detect_language(self, tree):
        res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:lang', namespaces=self.__namespaces)
        if len(res) == 0:
            use_namespaces = False
            res = tree.xpath('/FictionBook/description/title-info/lang')
        if len(res) > 0:
            self.language_code = res[0].text

    def __detect_tags(self, tree):
        res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:genre', namespaces=self.__namespaces)
        if len(res) == 0:
            use_namespaces = False
            res = tree.xpath('/FictionBook/description/title-info/genre')
        for node in res:
            self.__add_tag__(node.text)

    def __detect_series_info(self, tree):
        res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:sequence', namespaces=self.__namespaces)
        if len(res) == 0:
            use_namespaces = False
            res = tree.xpath('/FictionBook/description/title-info/sequence')
        if len(res) > 0:
            title = BookFile.__normalise_string__(res[0].get('name'))
            index = BookFile.__normalise_string__(res[0].get('number'))
            if title:
                self.series_info = {
                    'title': title,
                    'index': index or None
                }

    def __detect_description(self, tree):
        res = tree.xpath('/fb:FictionBook/fb:description/fb:title-info/fb:annotation', namespaces=self.__namespaces)
        if len(res) == 0:
            res = tree.xpath('/FictionBook/description/title-info/annotation')
        if len(res) > 0:
            return etree.tostring(res[0], encoding='utf-8', method='text')

        return None

class FB2(FB2Base):
    def __init__(self, file, original_filename):
        FB2Base.__init__(self, file, original_filename, Mimetype.FB2)

    def __create_tree__(self):
        try:
            self.file.seek(0, 0)
            return etree.parse(self.file)
        except:
            raise FB2StructureException('the file is not a valid XML')

    def __exit__(self, kind, value, traceback):
        pass

class FB2Zip(FB2Base):
    def __init__(self, file, original_filename):
        self.__zip_file = zipfile.ZipFile(file)
        try:
            if self.__zip_file.testzip():
                raise FB2StructureException('broken zip archive')
            self.__infos = list_zip_file_infos(self.__zip_file)
            if len(self.__infos) != 1:
                raise FB2StructureException('archive contains %s files' % len(self.__infos))
        except FB2StructureException as error:
            self.__zip_file.close()
            raise error
        except Exception as error:
            self.__zip_file.close()
            raise FB2StructureException(error)

        FB2Base.__init__(self, file, original_filename, Mimetype.FB2_ZIP)

    def __create_tree__(self):
        with self.__zip_file.open(self.__infos[0]) as entry:
            try:
                return etree.fromstring(entry.read(50 * 1024 * 1024))
            except:
                raise FB2StructureException('\'%s\' is not a valid XML' % self.__infos[0].filename)

    def __exit__(self, kind, value, traceback):
        self.__zip_file.__exit__(kind, value, traceback)
        pass
