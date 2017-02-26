import gzip, os
#from Crypto.Cipher import AES
from tempfile import mktemp

def encrypt(file_name, key, working_dir):
    '''
    file_name:     full path to file to encrypt
    key:           16 byte string
    working_dir:   directory to create temorary files
    '''
    # tmp_file_name = mktemp(dir=working_dir)
    # with open(file_name, 'rb') as istream:
    #     with gzip.open(tmp_file_name, 'wb') as ostream:
    #         ostream.writelines(istream)
    #
    # init_vector = os.urandom(16)
    #
    # mode = AES.MODE_CBC
    # encryptor = AES.new(key, mode, init_vector)
    #
    # with open(tmp_file_name, 'rb') as istream:
    #     with open(file_name, 'wb') as ostream:
    #         ostream.write(init_vector)
    #         while True:
    #             data = istream.read(8192)
    #             if len(data) == 8192:
    #                 ostream.write(encryptor.encrypt(data))
    #             else:
    #                 pad = 16 - len(data) % 16
    #                 ostream.write(encryptor.encrypt(data + pad * chr(pad)))
    #                 break
    #
    # os.remove(tmp_file_name)
    pass
