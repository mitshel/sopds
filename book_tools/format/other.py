from book_tools.format.bookfile import BookFile

class Dummy(BookFile):
    def __init__(self, file, original_filename, mimetype):
        BookFile.__init__(self, file, original_filename, mimetype)

    def __exit__(self, kind, value, traceback):
        pass