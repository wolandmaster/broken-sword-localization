#!/usr/bin/env python3
# Sandor Balazsi (sandor.balazsi@gmail.com)

def get_header_type(input_file, offset=0):
    pos = input_file.tell()
    try:
        input_file.seek(offset)
        header = input_file.read(12)
        if header[:4] == b'VT7A':
            return 'vt7a'
        elif header[:4] == b'RIFF':
            return 'webp'
        elif header[:4] == b'STRM':
            return 'stream'
        elif header[:4] == b'OggS':
            return 'ogg'
        elif header[:4] == b'TEXT':
            return 'txa'
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
        input_file.seek(pos)

def get_file_type(filename):
    with open(filename, 'rb') as input_file:
        return get_header_type(input_file)

def read_in_chunks(input_file, length, chunks_size=4096):
    while length > 0:
        data = input_file.read(min(length, chunks_size))
        if not data:
            raise exception("unexpected end of file: %s" % input_file.name)
        length -= len(data)
        yield data

def right_chop(string, ending):
    if string.endswith(ending):
        return string[:-len(ending)]
    return string

class dot_dict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

# vim: set ts=4:sts=4:sw=4:noet

