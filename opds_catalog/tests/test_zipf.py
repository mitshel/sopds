import os

from django.test import TestCase

from opds_catalog import zipf as zipfile

class zipTestCase(TestCase):
    test_module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_ROOTLIB = os.path.join(test_module_path, 'tests/data')
    test_zip = "books.zip"
    test_bad_zip = "badfile.zip"

    def setUp(self):
        pass

    def test_zip_valid(self):
        z = zipfile.ZipFile(os.path.join(self.test_ROOTLIB, self.test_zip), 'r', allowZip64=True)
        filelist = z.namelist()
        file_size = z.getinfo("539485.fb2").file_size
        file = z.open("539485.fb2")
        self.assertListEqual(filelist,["539603.fb2","539485.fb2","539273.fb2"])
        self.assertEquals(file_size,12293)
        self.assertEquals(file.read(38), b'<?xml version="1.0" encoding="utf-8"?>')
        file.close()


    def test_zip_novalid(self):
        bad_file_count = 0
        try:
            zipfile.ZipFile(os.path.join(self.test_ROOTLIB, self.test_bad_zip), 'r', allowZip64=True)
        except zipfile.BadZipFile:
            bad_file_count = 1

        self.assertEquals(bad_file_count, 1)


