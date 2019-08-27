#!/usr/bin/env python3
# sandor.balazsi@gmail.com

import argparse, os, sys, tempfile, zlib

#############
# T O O L S #
#############
def get_file_type(file, offset=0):
    pos = file.tell()
    try:
        file.seek(offset)
        header = file.read(12)
        if header[:4] == b'VT7A':
            return 'vt7a'
        elif header[:4] == b'RIFF':
            return 'webp'
        elif header[:4] == b'STRM':
            return 'stream'
        elif header[:4] == b'OggS':
            return 'ogg'
        elif header[:2] == b'\x78\x9c':
            return 'zlib'
        elif header[:6] == b'<?xml ':
            return 'xml'
        elif header[:11] == b'<functions>':
            return 'funct.xml'
        elif header[4:12] == b'\x66\x74\x79\x70\x4D\x34\x56\x20':
            return 'm4v'
        else:
            return 'dat'
    finally:
        file.seek(pos)

def read_in_chunks(file, length, chunks_size=4096):
    while length > 0:
        data = file.read(min(length, chunks_size))
        if not data:
            raise exception("unexpected end of file: %s" % file.name)
        length -= len(data)
        yield data

def right_chop(string, ending):
    if string.endswith(ending):
        return string[:-len(ending)]
    return string

#################
# A C T I O N S #
#################
def test(source):
    print('zlib archive: %r' % (get_file_type(source) == 'zlib'))

def compress(source):
    temp_fd, temp_file = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'wb') as temp:
        try:
            compressor = zlib.compressobj()
            for chunk in read_in_chunks(source, os.path.getsize(source.name), 65536):
                temp.write(compressor.compress(chunk))
                temp.write(compressor.flush(zlib.Z_FULL_FLUSH))
            os.rename(temp_file, source.name + '.zlib')
            os.remove(source.name)
            return source.name + '.zlib'
        except zlib.error as e:
            os.remove(temp_file)
            sys.stderr.write('pack failed of "%s": %s\n' % (source.name, e))
            sys.exit(1)

def decompress(source):
    temp_fd, temp_file = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'wb+') as temp:
        try:
            decompressor = zlib.decompressobj()
            for chunk in read_in_chunks(source, os.path.getsize(source.name), 65536):
                temp.write(decompressor.decompress(chunk))
                temp.write(decompressor.flush(zlib.Z_FULL_FLUSH))
            target_name = right_chop(source.name, '.zlib')
            if source.name == target_name or os.path.splitext(target_name)[1] == '':
                target_name += '.' + get_file_type(temp)
            os.rename(temp_file, target_name)
            os.remove(source.name)
            return target_name
        except zlib.error as e:
            os.remove(temp_file)
            sys.stderr.write('unpack failed of "%s": %s\n' % (source.name, e))
            sys.exit(1)

###########
# M A I N #
###########
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compress or decompress file with zlib.', add_help=False)
    parser.add_argument('source', help='input file', type=argparse.FileType('rb'), metavar='FILE')

    operation = parser.add_argument_group('operation')
    action = operation.add_mutually_exclusive_group(required=True)
    action.add_argument('-t', '--test', help='check whether is a zlib archive',
            action='store_const', dest='action', const='test')
    action.add_argument('-c', '--compress', help='compress input file',
            action='store_const', dest='action', const='compress')
    action.add_argument('-d', '--decompress', help='decompress zlib archive',
            action='store_const', dest='action', const='decompress')
    operation.add_argument('-h', '--help', help='show this help message and exit', action='help')

    args = parser.parse_args()
    locals()[args.action](args.source)

# vim: set ts=4:sts=4:sw=4:noet

