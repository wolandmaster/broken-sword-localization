#!/usr/bin/env python3
# Broken Sword 5 vt7a file tool
# by Sandor Balazsi (sandor.balazsi@gmail.com)
#
# Format specification information:
# =================================
# OVERALL LAYOUT:
#   HEADER [1]
#   FILE ENTRY [N] + null padding to a multiple of 4096 bytes
#   FILE DATA [N]
#
# HEADER:
#   4 bytes - Id (VT7A)
#   4 bytes - Version (2)
#   4 bytes - Unknown
#   4 bytes - Number of files
#
# FILE ENTRY:
#   4 bytes - Filename hash (for each char in filename: hash = hash<<7 + hash<<1 + hash + char)
#   4 bytes - File data offset
#   4 bytes - Decompressed file length
#   4 bytes - Compressed file length (0 = not compressed)
#
# FILE DATA:
#   N bytes - File data (uncompressed or zlib compressed)
#   N bytes - Null padding to a multiple of 4096 bytes

import argparse, os, sys, struct
sys.dont_write_bytecode = True
import bs5_zlib

###############
# C O N F I G #
###############
DEFAULT_NAME_HASH_FILE = 'bs5_name_hash.txt'
NAME_HASH = {}
EXTRACT_CHUNK_SIZE = 64 * 1024

#############
# T O O L S #
#############
class dot_dict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

def open_name_hash(filename):
    name_hash = {}
    if not os.path.isfile(filename):
        print('warning: name hash file (%s) does not exists!' % filename)
    else:
        with open(filename) as file:
            for line in file:
                if line.startswith('#'):
                    continue
                hash, name = line.partition(' ')[::2]
                name_hash[int(hash)] = name.strip()
    return name_hash

def resolve_entry_name(file, entry, subfolder=''):
    file_type = bs5_zlib.get_file_type(file, entry.offset)
    if entry.hash in NAME_HASH:
        zlib_ext = '.zlib' if file_type == 'zlib' else ''
        return os.path.join(subfolder, NAME_HASH.get(entry.hash) + zlib_ext), True
    else:
        return os.path.join(subfolder, '%u.%s' % (entry.hash, file_type)), False

###########
# L I S T #
###########
def read(file, format):
    data = file.read(struct.calcsize(format))
    return struct.unpack(format, data)

def read_header(file):
    keys = ('id', 'version', 'unknown', 'file_count')
    return dot_dict(dict(zip(keys, read(file, '=4sLLL'))))

def read_entry(file):
    keys = ('hash', 'offset', 'size', 'compressed_size')
    return dot_dict(dict(zip(keys, read(file, '=LLLL'))))

def list(args):
    header = read_header(args.source_file)
    entries = [
        ['name', 'hash', 'offset', 'size', 'compressed'],
        ['====', '====', '======', '====', '==========']
    ]
    for i in range(header.file_count):
        entry = read_entry(args.source_file)
        name, known = resolve_entry_name(args.source_file, entry)
        if args.decompress and name.endswith('.zlib'):
            name = name[:-5]
            if os.path.splitext(name)[1] == '':
                name += '.tbd'
        if known or not args.skip_unknown:
            entries.append([name, '%u' % entry.hash, '0x%x' % entry.offset,
                '%u' % entry.size, '%u' % entry.compressed_size])
    widths = [max(map(len, col)) for col in zip(*entries)]
    for row in entries:
        print('  '.join((value.ljust(width) for value, width in zip(row, widths))))

#################
# E X T R A C T #
#################
def extract_entry(source_file, entry, target_name):
    dirname = os.path.dirname(target_name)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    pos = source_file.tell()
    try:
        source_file.seek(entry.offset)
        with open(target_name, 'wb+') as target_file:
            length = entry.size if entry.compressed_size == 0 else entry.compressed_size
            for chunk in bs5_zlib.read_in_chunks(source_file, length, EXTRACT_CHUNK_SIZE):
                target_file.write(chunk)
    finally:
        source_file.seek(pos)

def extract(args):
    header = read_header(args.source_file)
    for i in range(header.file_count):
        entry = read_entry(args.source_file)
        target_name, known = resolve_entry_name(args.source_file, entry, args.target_dir)
        if known or not args.skip_unknown:
            print(target_name)
            extract_entry(args.source_file, entry, target_name)
            if args.decompress:
                with open(target_name, 'rb') as file:
                    if bs5_zlib.get_file_type(file) == 'zlib':
                        target_name = bs5_zlib.decompress(file)
                        print(target_name)
            if args.recursive:
                with open(target_name, 'rb') as file:
                    if bs5_zlib.get_file_type(file) == 'vt7a':
                        extract(dot_dict({
                            'source_file': file,
                            'target_dir': os.path.splitext(target_name)[0],
                            'skip_unknown': args.skip_unknown,
                            'decompress': args.decompress,
                            'recursive':  args.recursive
                        }))

###############
# C R E A T E #
###############
def write(file, format, *data):
    file.write(struct.pack(format, *data))

def create(args):
    pass

###########
# M A I N #
###########
class SingleMetavarHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super(SingleMetavarHelpFormatter, self).__init__(prog, max_help_position=26)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return self._metavar_formatter(action, action.dest)(1)[0]
        else:
            parts = action.option_strings.copy()
            if action.nargs != 0:
                parts[-1] += '=%s' % self._format_args(action, action.dest.upper())
            return ', '.join(parts)

class FileAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, value)
        setattr(namespace, 'target_dir', os.path.splitext(value.name)[0])
        setattr(namespace, 'target_file', value.name + '.new')

parser = argparse.ArgumentParser(description='Broken Sword 5 vt7a archive tool '
        + 'by Sandor Balazsi (sandor.balazsi@gmail.com)', add_help=False,
        epilog='Mandatory or optional arguments to long options are also mandatory or optional '
            + 'for any corresponding short options.', formatter_class=SingleMetavarHelpFormatter)
parser.add_argument('source_file', help='input/output vt7a file', type=argparse.FileType('rb'),
        metavar='FILE', action=FileAction)

operation = parser.add_argument_group('main operation')
action = operation.add_mutually_exclusive_group(required=True)
action.add_argument('-l', '--list', help='list files in a vt7a archive',
        action='store_const', dest='action', const='list')
action.add_argument('-x', '--extract', help='extract files from a vt7a archive',
        action='store_const', dest='action', const='extract')
action.add_argument('-c', '--create', help='create new vt7a archive',
        action='store_const', dest='action', const='create')

optional = parser.add_argument_group('optional arguments')
optional.add_argument('-h', '--help', help='show this help message and exit', action='help')
optional.add_argument('-H', '--hash', help='name hash file (default: %(default)s)',
        metavar='HASH-FILE', dest='name_hash_file', default=DEFAULT_NAME_HASH_FILE)
optional.add_argument('-s', '--skip-unknown', help='skip entries with unknown name hash', action='store_true')

extract_group = parser.add_argument_group('extract arguments')
extract_group.add_argument('-t', '--target', help='target dir for extract (default: <FILE> w/o ext)',
        metavar='DIR', dest='target_dir')
extract_group.add_argument('-d', '--decompress', help='decompress extracted zlib files', action='store_true')
extract_group.add_argument('-r', '--recursive', help='operate recursively on extracted vt7a files', action='store_true')

create_group = parser.add_argument_group('create arguments')
create_group.add_argument('-o', '--output', help='output vt7a file name (default: <FILE>.new)',
        metavar='DEST-FILE', dest='target_file')

args = parser.parse_args()
NAME_HASH = open_name_hash(args.name_hash_file)
if bs5_zlib.get_file_type(args.source_file) != 'vt7a':
    print('not a vt7a file: %s' % args.source_file.name)
    sys.exit(1)
locals()[args.action](args)

# vim: set ts=4:sts=4:sw=4:noet

