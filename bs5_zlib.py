#!/usr/bin/env python3
# Compress or decompress file with zlib
# by Sandor Balazsi (sandor.balazsi@gmail.com)

import argparse, os, sys, tempfile, zlib
sys.dont_write_bytecode = True
from bs5_common import *

###############
# C O N F I G #
###############
SCRIPT = os.path.basename(__file__)
CHUNK_SIZE = 64 * 1024

###############
# C O M M O N #
###############
def verify_file_type_zlib(source_file):
    if get_header_type(source_file) != 'zlib':
        sys.stderr.write('%s: %s: not in zlib format\n' % (SCRIPT, source_file.name))
        sys.exit(1)

#################
# A C T I O N S #
#################
def test(source_file):
    verify_file_type_zlib(source_file)
    decompressor = zlib.decompressobj()
    try:
        for chunk in read_in_chunks(source_file, os.path.getsize(source_file.name), CHUNK_SIZE):
            decompressor.decompress(chunk)
    except zlib.error as e:
        sys.stderr.write('%s: %s: %s\n' % (SCRIPT, source_file.name, e))
        sys.exit(1)

def compress(source_file):
    temp_fd, temp_filename = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'wb') as temp_file:
        try:
            compressor = zlib.compressobj()
            for chunk in read_in_chunks(source_file, os.path.getsize(source_file.name), CHUNK_SIZE):
                temp_file.write(compressor.compress(chunk))
                temp_file.write(compressor.flush(zlib.Z_FULL_FLUSH))
            os.rename(temp_filename, source_file.name + '.zlib')
            os.remove(source_file.name)
            return source_file.name + '.zlib'
        except zlib.error as e:
            os.remove(temp_filename)
            sys.stderr.write('%s: %s: compress failed: %s\n' % (SCRIPT, source_file.name, e))
            sys.exit(1)

def decompress(source_file):
    verify_file_type_zlib(source_file)
    temp_fd, temp_filename = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'wb+') as temp_file:
        try:
            decompressor = zlib.decompressobj()
            for chunk in read_in_chunks(source_file, os.path.getsize(source_file.name), CHUNK_SIZE):
                temp_file.write(decompressor.decompress(chunk))
                temp_file.write(decompressor.flush(zlib.Z_FULL_FLUSH))
            target_name = right_chop(source_file.name, '.zlib')
            if source_file.name == target_name or os.path.splitext(target_name)[1] == '':
                target_name += '.' + get_header_type(temp_file)
            os.rename(temp_filename, target_name)
            os.remove(source_file.name)
            return target_name
        except zlib.error as e:
            os.remove(temp_filename)
            sys.stderr.write('%s: %s: decompress failed: %s\n' % (SCRIPT, source_file.name, e))
            sys.exit(1)

###########
# M A I N #
###########
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compress or decompress file with zlib.', add_help=False)
    parser.add_argument('source_file', help='input file', type=argparse.FileType('rb'), metavar='FILE')

    operation = parser.add_argument_group('operation')
    action = operation.add_mutually_exclusive_group(required=True)
    action.add_argument('-t', '--test', help='test compressed file integrity',
            action='store_const', dest='action', const='test')
    action.add_argument('-c', '--compress', help='compress input file',
            action='store_const', dest='action', const='compress')
    action.add_argument('-d', '--decompress', help='decompress zlib archive',
            action='store_const', dest='action', const='decompress')
    operation.add_argument('-h', '--help', help='show this help message and exit', action='help')

    args = parser.parse_args()
    locals()[args.action](args.source_file)

# vim: set ts=4:sts=4:sw=4:noet

