import os, shutil, urllib, zipfile
from lxml import etree
from tempfile import mktemp

from book_tools.format.aes import encrypt
from book_tools.format.bookfile import BookFile
from book_tools.format.mimetype import Mimetype
from book_tools.format.util import list_zip_file_infos

class EPub(BookFile):
    class Issue(object):
        FIRST_ITEM_NOT_MIMETYPE = 1
        MIMETYPE_ITEM_IS_DEFLATED = 2

    class Namespace(object):
        XHTML = 'http://www.w3.org/1999/xhtml'
        CONTAINER = 'urn:oasis:names:tc:opendocument:xmlns:container'
        OPF = 'http://www.idpf.org/2007/opf'
        DUBLIN_CORE = 'http://purl.org/dc/elements/1.1/'
        ENCRYPTION = 'http://www.w3.org/2001/04/xmlenc#'
        DIGITAL_SIGNATURE = 'http://www.w3.org/2000/09/xmldsig#'
        MARLIN = 'http://marlin-drm.com/epub'
        CALIBRE = 'http://calibre.kovidgoyal.net/2009/metadata'

    class Entry(object):
        MIMETYPE = 'mimetype'
        MANIFEST = 'META-INF/manifest.xml'
        METADATA = 'META-INF/metadata.xml'
        CONTAINER = 'META-INF/container.xml'
        ENCRYPTION = 'META-INF/encryption.xml'
        RIGHTS = 'META-INF/rights.xml'
        SIGNATURES = 'META-INF/signatures.xml'

    TOKEN_URL = 'https://books.fbreader.org/drm/marlin/get-token'
    CONTENT_ID_PREFIX = 'urn:marlin:organization:fbreader.org:0001:'

    ALGORITHM_EMBEDDING = 'http://www.idpf.org/2008/embedding'
    ALGORITHM_AES128 = Namespace.ENCRYPTION + 'aes128-cbc'

    class StructureException(Exception):
        def __init__(self, message):
            Exception.__init__(self, 'ePub verification failed: ' + message)

    def __init__(self, file, original_filename):
        BookFile.__init__(self, file, original_filename, Mimetype.EPUB)
        self.root_filename = None
        self.cover_fileinfos = []

        self.__zip_file = None
        self.__initialize()

    def __initialize(self):
        self.__zip_file = zipfile.ZipFile(self.file)
        self.issues = []
        try:
            if self.__zip_file.testzip():
                raise EPub.StructureException('broken zip archive')

            infos = self.__zip_file.infolist()
            if len(infos) == 0:
                raise EPub.StructureException('empty zip archive')

            mimetype_info = infos[0]
            if mimetype_info.filename != EPub.Entry.MIMETYPE:
                self.issues.append(EPub.Issue.FIRST_ITEM_NOT_MIMETYPE)
            elif mimetype_info.compress_type != zipfile.ZIP_STORED:
                self.issues.append(EPub.Issue.MIMETYPE_ITEM_IS_DEFLATED)

            with self.__zip_file.open(EPub.Entry.MIMETYPE) as mimetype_file:
                if mimetype_file.read(30).decode().rstrip('\n\r') != Mimetype.EPUB:
                    raise EPub.StructureException('\'mimetype\' item content is incorrect')

            self.__extract_metainfo()
        except EPub.StructureException as error:
            self.close()
            raise error
        except Exception as error:
            self.close()
            raise EPub.StructureException(error.message)

    def close(self):
        self.__zip_file.close()

    def __exit__(self, kind, value, traceback):
        self.__zip_file.__exit__(kind, value, traceback)

    def __etree_from_entry(self, info):
        with self.__zip_file.open(info) as entry:
            try:
                return etree.fromstring(entry.read(1048576))
            except:
                raise EPub.StructureException('\'' + info.filename + '\' is not a valid XML')

    def __extract_metainfo(self):
        root_info = self.__get_root_info()
        self.root_filename = root_info.filename
        tree = self.__etree_from_entry(root_info)
        namespaces = {'opf': EPub.Namespace.OPF, 'dc': EPub.Namespace.DUBLIN_CORE}

        res = tree.xpath('/opf:package/opf:metadata/dc:title', namespaces=namespaces)
        if len(res) > 0:
            self.__set_title__(res[0].text)

        res = tree.xpath('/opf:package/opf:metadata/dc:creator[@role="aut"]', namespaces=namespaces)
        if len(res) == 0:
            res = tree.xpath('/opf:package/opf:metadata/dc:creator', namespaces=namespaces)
        for node in res:
            self.__add_author__(node.text)

        res = tree.xpath('/opf:package/opf:metadata/dc:language', namespaces=namespaces)
        if len(res) > 0 and res[0].text:
            self.language_code = res[0].text.strip()

        res = tree.xpath('/opf:package/opf:metadata/dc:subject', namespaces=namespaces)
        for node in res:
            self.__add_tag__(node.text)

        res = tree.xpath('/opf:package/opf:metadata/opf:meta[@name="calibre:series"]', namespaces=namespaces)
        if len(res) > 0:
            series = BookFile.__normalise_string__(res[0].get('content'))
            if series:
                res = tree.xpath('/opf:package/opf:metadata/opf:meta[@name="calibre:series_index"]', namespaces=namespaces)
                index = BookFile.__normalise_string__(res[0].get('content')) if len(res) > 0 else None
                self.series_info = {
                    'title': series,
                    'index': index or None
                }

        res = tree.xpath('/opf:package/opf:metadata/dc:description', namespaces=namespaces)
        if len(res) > 0 and res[0].text:
            self.description = res[0].text.strip()

        prefix = os.path.dirname(root_info.filename)
        if prefix:
            prefix += '/'
        self.cover_fileinfos = self.__find_cover(tree, prefix)

    def __find_cover(self, tree, prefix):
        namespaces = {'opf': EPub.Namespace.OPF, 'dc': EPub.Namespace.DUBLIN_CORE}

        def xpath(query):
            return tree.xpath(query, namespaces=namespaces)[0]

        def item_for_href(ref):
            return xpath('/opf:package/opf:manifest/opf:item[@href="%s"]' % ref)

        def image_infos(node):
            path = os.path.normpath(prefix + node.get('href'))
            try:
                fileinfo = self.__zip_file.getinfo(path)
            except:
                fileinfo = self.__zip_file.getinfo(urllib.unquote(path))
            mime = node.get('media-type')
            info = {
                'filename': fileinfo.filename,
                'mime': mime
            }
            if mime.startswith('image/'):
                return [info]
            elif mime == 'application/xhtml+xml':
                xhtml = self.__etree_from_entry(fileinfo)
                xhtml_prefix = os.path.dirname(fileinfo.filename) + '/'
                img = xhtml.xpath('//xhtml:img[@src]', namespaces={'xhtml': EPub.Namespace.XHTML})[0]
                return [info,
                    {
                        'filename': os.path.normpath(xhtml_prefix + img.get('src')),
                        # TODO: detect mimetype
                        'mime': 'image/auto'
                    }
                ]
            else:
                raise Exception('unknown mimetype %s' % mime)

        try:
            return image_infos(xpath('/opf:package/opf:manifest/opf:item[@properties="cover-image"]'))
        except:
            pass

        try:
            node = xpath('/opf:package/opf:metadata/opf:meta[@name="cover"]')
            return image_infos(xpath('/opf:package/opf:manifest/opf:item[@id="%s"]' % node.get('content')))
        except:
            pass

        try:
            node = xpath('/opf:package/opf:metadata/meta[@name="cover"]')
            return image_infos(xpath('/opf:package/opf:manifest/opf:item[@id="%s"]' % node.get('content')))
        except:
            pass

        try:
            node = xpath('/package/metadata/meta[@name="cover"]')
            return image_infos(xpath('/package/manifest/item[@id="%s"]' % node.get('content')))
        except:
            pass

        try:
            node = xpath('/opf:package/opf:guide/opf:reference[@type="other.ms-coverimage-standard"][@title="Cover"]')
            return image_infos(item_for_href(node.get('href')))
        except:
            pass

        try:
            node = xpath('/opf:package/opf:guide/opf:reference[@type="other.ms-coverimage-standard"]')
            return image_infos(item_for_href(node.get('href')))
        except:
            pass

        try:
            return image_infos(xpath('/opf:package/opf:manifest/opf:item[@id="cover"]'))
        except:
            pass

        return []

    def __get_root_info(self):
        try:
            container_info = self.__zip_file.getinfo(EPub.Entry.CONTAINER)
        except:
            container_info = None
        if container_info:
            tree = self.__etree_from_entry(container_info)
            root_file = None
            namespaces = {'cont': EPub.Namespace.CONTAINER}
            res = tree.xpath('/cont:container/cont:rootfiles/cont:rootfile', namespaces=namespaces)
            if len(res) == 1 and res[0].get('media-type') == 'application/oebps-package+xml':
                root_file = res[0].get('full-path')
            if root_file:
                return self.__zip_file.getinfo(root_file)
        else:
            opf_infos = [i for i in self.__zip_file.infolist() if i.filename.endswith('.opf')]
            if len(opf_infos) > 1:
                raise EPub.StructureException('several OPF files in the archive')
            elif len(opf_infos) == 1:
                return opf_infos[0]

        raise EPub.StructureException('OPF entry not found')

    def __contains_entry(self, name):
        try:
            self.__zip_file.getinfo(name)
            return True
        except KeyError:
            return False

    def __extract_content_ids(self):
        content_ids = set()
        try:
            tree = self.__etree_from_entry(EPub.Entry.ENCRYPTION)
            ns = {
                'c': EPub.Namespace.CONTAINER,
                'e': EPub.Namespace.ENCRYPTION,
                'd': EPub.Namespace.DIGITAL_SIGNATURE
            }
            res = tree.xpath('/c:encryption/e:EncryptedData/d:KeyInfo/d:KeyName', namespaces=ns)
            for node in res:
                key_name = res[0].text
                if key_name and key_name.startswith(EPub.CONTENT_ID_PREFIX):
                    content_ids.add(key_name[len(EPub.CONTENT_ID_PREFIX):])
        except:
            pass
        return list(content_ids)

    def get_encryption_info(self):
        UNKNOWN_ENCRYPTION = { 'method': 'unknown' }

        algo = None

        if self.__contains_entry(EPub.Entry.ENCRYPTION):
            try:
                tree = self.__etree_from_entry(EPub.Entry.ENCRYPTION)
                namespaces = {'c': EPub.Namespace.CONTAINER, 'e':EPub.Namespace.ENCRYPTION}
                res = tree.xpath('/c:encryption/e:EncryptedData/e:EncryptionMethod', namespaces=namespaces)
                algorithms = list(set([r.get('Algorithm') for r in res]))
                if len(algorithms) != 1:
                    return {'method': 'multi', 'ids': algorithms}
                if algorithms[0] == EPub.ALGORITHM_EMBEDDING:
                    return {'method': 'embedding'}
                elif algorithms[0] == EPub.ALGORITHM_AES128:
                    algo = algorithms[0]
                else:
                    return UNKNOWN_ENCRYPTION
            except:
                return UNKNOWN_ENCRYPTION

        if self.__contains_entry(EPub.Entry.RIGHTS):
            if algo == EPub.ALGORITHM_AES128:
                try:
                    tree = self.__etree_from_entry(EPub.Entry.RIGHTS)
                    namespaces = {'m': EPub.Namespace.MARLIN}
                    res = tree.xpath('/m:Marlin/m:RightsURL/m:RightsIssuer/m:URL', namespaces=namespaces)
                    if res:
                        token_url = res[0].text
                        content_ids = self.__extract_content_ids() if token_url == EPub.TOKEN_URL else []
                        return {
                            'method': 'marlin',
                            'token_url': token_url,
                            'content_ids': content_ids
                        }
                except:
                    pass
            return UNKNOWN_ENCRYPTION

        if self.__contains_entry(EPub.Entry.SIGNATURES):
            return UNKNOWN_ENCRYPTION

        return {}

    def __save_tree(self, zip_file, filename, tree, working_dir):
        path = os.path.join(working_dir, filename)
        with open(path, 'w') as pfile:
            tree.write(pfile, pretty_print=True)
        zip_file.write(path, arcname=filename)

    def __add_encryption_section(self, index, root, uri, content_id):
        # See http://www.marlin-community.com/files/marlin-EPUB-extension-v1.0.pdf
        # section 4.2.1
        key_name = EPub.CONTENT_ID_PREFIX + content_id

        enc_data = etree.SubElement(root, etree.QName(EPub.Namespace.ENCRYPTION, 'EncryptedData'), Id='ED%d' % index)
        etree.SubElement(enc_data, etree.QName(EPub.Namespace.ENCRYPTION, 'EncryptionMethod'), Algorithm=EPub.Namespace.ENCRYPTION + 'aes128-cbc')
        key_info = etree.SubElement(enc_data, etree.QName(EPub.Namespace.DIGITAL_SIGNATURE, 'KeyInfo'))
        key_name_tag = etree.SubElement(key_info, etree.QName(EPub.Namespace.DIGITAL_SIGNATURE, 'KeyName'))
        key_name_tag.text = key_name
        cipher_data = etree.SubElement(enc_data, etree.QName(EPub.Namespace.ENCRYPTION, 'CipherData'))
        etree.SubElement(cipher_data, etree.QName(EPub.Namespace.ENCRYPTION, 'CipherReference'), URI=uri)

    def __create_encryption_file(self, zip_file, working_dir, encrypted_files, content_id):
        namespaces = {
            None    :   EPub.Namespace.CONTAINER,
            'enc'   :   EPub.Namespace.ENCRYPTION,
            'ds'    :   EPub.Namespace.DIGITAL_SIGNATURE
        }
        root = etree.Element(etree.QName(EPub.Namespace.CONTAINER, 'encryption'), nsmap=namespaces)
        tree = etree.ElementTree(root)

        index = 1
        for filename in encrypted_files:
            self.__add_encryption_section(index, root, filename, content_id)
            index += 1

        self.__save_tree(zip_file, EPub.Entry.ENCRYPTION, tree, working_dir)

    def __create_rights_file(self, zip_file, working_dir):
        namespaces = {None: EPub.Namespace.MARLIN}
        root = etree.Element(etree.QName(EPub.Namespace.MARLIN, 'Marlin'), nsmap=namespaces)
        tree = etree.ElementTree(root)
        etree.SubElement(root, etree.QName(EPub.Namespace.MARLIN, 'Version')).text = '1.0'
        rights_url = etree.SubElement(root, etree.QName(EPub.Namespace.MARLIN, 'RightsURL'))
        rights_issuer = etree.SubElement(rights_url, etree.QName(EPub.Namespace.MARLIN, 'RightsIssuer'))
        etree.SubElement(rights_issuer, etree.QName(EPub.Namespace.MARLIN, 'URL')).text = EPub.TOKEN_URL
        self.__save_tree(zip_file, EPub.Entry.RIGHTS, tree, working_dir)

    def encrypt(self, key, content_id, working_dir, files_to_keep=None):
        if self.get_encryption_info():
            raise Exception('Cannot encrypt file %s, it is already encrypted' % self.file.name)

        if not files_to_keep:
            files_to_keep = [EPub.Entry.MANIFEST, EPub.Entry.METADATA, EPub.Entry.CONTAINER]
            files_to_keep += [self.root_filename]
            files_to_keep += [info['filename'] for info in self.cover_fileinfos]

        self.__zip_file.extractall(path=working_dir)

        new_epub = mktemp(dir=working_dir)
        with zipfile.ZipFile(new_epub, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(EPub.Entry.MIMETYPE, Mimetype.EPUB, zipfile.ZIP_STORED)
            encrypted_files = []
            for entry in [info.filename for info in list_zip_file_infos(self.__zip_file) if info.filename != EPub.Entry.MIMETYPE]:
                path = os.path.join(working_dir, entry)
                if entry in files_to_keep:
                    zip_file.write(path, arcname=entry)
                else:
                    encrypt(os.path.join(working_dir, entry), key, working_dir)
                    encrypted_files.append(entry)
                    zip_file.write(path, arcname=entry, compress_type=zipfile.ZIP_STORED)
            self.__create_encryption_file(zip_file, working_dir, encrypted_files, content_id)
            self.__create_rights_file(zip_file, working_dir)
        shutil.move(new_epub, self.path)
        self.close()
        self.__initialize()

    def repair(self, working_dir):
        self.__zip_file.extractall(path=working_dir)

        new_epub = mktemp(dir=working_dir)
        with zipfile.ZipFile(new_epub, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(EPub.Entry.MIMETYPE, Mimetype.EPUB, zipfile.ZIP_STORED)
            for entry in [info.filename for info in list_zip_file_infos(self.__zip_file) if info.filename != EPub.Entry.MIMETYPE]:
                zip_file.write(os.path.join(working_dir, entry), arcname=entry)
        shutil.move(new_epub, self.path)
        self.close()
        self.__initialize()

    def extract_cover_internal(self, working_dir):
        if len(self.cover_fileinfos) == 0:
            return (None, False)
        name = self.cover_fileinfos[-1]['filename']
        self.__zip_file.extract(name, path=working_dir)
        split = [part for part in name.split('/') if part]
        if len(split) > 1:
            shutil.move(os.path.join(working_dir, name), os.path.join(working_dir, split[-1]))
            shutil.rmtree(os.path.join(working_dir, split[0]))
        return (split[-1] if len(split) > 0 else None, False)
