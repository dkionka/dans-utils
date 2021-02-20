#!/usr/bin/env python3
#
# Copyright (c) 2021 Daniel P. Kionka; all rights reserved
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#
# pictree: Find pictures in a directory tree.
#
# TODO:
# - readable date format in summary
#

import argparse
import os
import re
import subprocess
import sys

# variables

# constants
PROG = os.path.basename(sys.argv[0])
extensions = [
        '.3gp', '.avi', '.wmv', '.flv', '.gif', '.heic', '.jpeg', '.jpg',
        '.mov', '.mp3', '.mp4', '.mpg', '.mts', '.png']
# dict keys
cksm_key = 'cksm'
dupl_key = 'dupl'
size_key = 'size'
time_key = 'time'
# misc
min_dupl_size = 7
checksum_prog = 'sha256sum' # external program name
def_checksum_val = '-'
space_subst = '|' # char never used in filenames

# parameters
debug = False
verbose = False

# utility functions

def debug_print(*args):
    if debug:
        print(*args, file=sys.stderr)
        sys.stderr.flush()

def prog_print(*args):
    print(PROG + ":", end=" ", file=sys.stderr)
    print(*args, file=sys.stderr)
    sys.stderr.flush()

def verbose_print(*args):
    if verbose:
        prog_print(*args)

def error_print(*args):
    prog_print(*args)
    sys.exit(1)

def replace_space(pic):
    return re.sub(' ', space_subst, pic)

def restore_space(pic):
    sub_re = '\\' + space_subst # must quote special char
    return re.sub(sub_re, ' ', pic)

# feature functions

def read_summary(sum_in):
    verbose_print('read_summary:', sum_in)
    info = {}
    with open(sum_in, 'r') as sum:
        for line in sum:
            words = line.split()
            rec = {}
            pic = restore_space(words[0])
            rec[cksm_key] = words[1]
            rec[size_key] = int(words[2])
            rec[time_key] = words[3]
            if len(words) > 4:
                rec[dupl_key] = restore_space(words[4])
            debug_print(pic, ':', rec)
            info[pic] = rec
    return info
    verbose_print('read_summary: Succeeded')

def find_pics(dirs_in):
    verbose_print('find_pics: dirs_in=%s' % (dirs_in))
    found = []

    for dir in dirs_in:
        for root, dirs, files in os.walk(dir):
            debug_print("dirs =", dirs, " files =", files)
            for filename in files:
                base, ext = os.path.splitext(filename)
                if ext.lower() in extensions:
                    full = os.path.join(root, filename)
                    found.append(full)
                    debug_print(full)

    verbose_print("find_pics: List...")
    for file in found:
        verbose_print(file)

    found.sort()
    verbose_print('find_pics: Succeeded')
    return found

def get_details(pics):
    verbose_print('get_details: len(pics)=%d' % (len(pics)))
    info = {}
    for pic in pics:
        rec = {}
        # stat info
        stat = os.lstat(pic)
        debug_print('pic=' + pic + ':', stat)
        size = 0
        time = 0
        if stat:
            size = stat.st_size
            time = stat.st_mtime
        else:
            verbose_print("stat error")
        rec[size_key] = size
        rec[time_key] = time
        # checksum info
        sum_str = ''
        if not "'" in pic: # cannot have quote in name
            sum_out = subprocess.check_output(
                    checksum_prog + " '" + pic + "'", shell=True)
            sum_str = re.sub(' .*', '', sum_out.decode().strip())
        if not len(sum_str):
            sum_str = def_checksum_val # cannot be empty
        rec[cksm_key] = sum_str
        debug_print(pic, ':', rec)
        # save to dic
        info[pic] = rec
    verbose_print('get_details: Succeeded')
    return info

def find_duplicates(info):
    base_to_pic = {} # lists of names with same basename
    cksm_to_pic = {} # lists of names with same checksum
    for pic in info:
        # for duplicate names
        base = os.path.basename(pic)
        if len(base) > min_dupl_size: # skip names like 001.jpg
            plist = base_to_pic[base] if base in base_to_pic else []
            debug_print("base=%s, len=%d" % (base, len(plist)))
            plist.append(pic)
            base_to_pic[base] = plist
        # for duplicate checksums
        cksm = info[pic][cksm_key]
        plist = cksm_to_pic[cksm] if cksm in cksm_to_pic else []
        debug_print("cksm=%s, len=%d" % (cksm, len(plist)))
        plist.append(pic)
        cksm_to_pic[cksm] = plist
    # find biggest of all pics with duplicate basenames
    for base in base_to_pic:
        plist = base_to_pic[base]
        if len(plist) > 1:
            # TODO: check for same time?
            debug_print("multiple basenames:", plist)
            size = -1
            for pic in plist:
                if info[pic][size_key] > size:
                    size = info[pic][size_key]
                    biggest = pic
            for pic in plist:
                if pic is not biggest:
                    info[pic][dupl_key] = biggest
    # find longest basename of all pics with duplicate checksums
    # TODO: use oldest copy of file
    for cksm in cksm_to_pic:
        plist = cksm_to_pic[cksm]
        if len(plist) > 1:
            debug_print("multiple checksums:", plist)
            size = -1
            for pic in plist:
                blen = len(os.path.basename(pic))
                if blen > size:
                    size = blen
                    biggest = pic
            for pic in plist:
                if pic is not biggest:
                    info[pic][dupl_key] = biggest

def write_db(info, sum_out):
    verbose_print('write_db: len(info)=%d, sum_out=%s' % (len(info), sum_out))
    if not sum_out:
        return
    with open(sum_out, 'w') as sum:
        for pic in info:
            rec = info[pic]
            line = '%s %s %d %s' % (
                    replace_space(pic), rec[cksm_key],
                    rec[size_key], rec[time_key])
            if dupl_key in rec:
                line += ' ' + replace_space(rec[dupl_key])
            verbose_print(line)
            sum.write(line + '\n')

def copy_tree(info, info2, dir_out):
    verbose_print('copy_tree: dir_out=%s' % (dir_out))
    for pic in info:
        rec = info[pic]
        base = os.path.basename(pic)
        dir_suffix = 0
        linked = False
        skip = False
        if dupl_key in rec:
            skip = True # skip link loop
        # filter pics in info2
        debug_print("filter:", len(info2))
        for pic2 in info2:
            debug_print('pic=%s,%s, pic2=%s,%s' %
                    (pic, rec[cksm_key], pic2, info2[pic2][cksm_key]))
            if rec[cksm_key] == info2[pic2][cksm_key]:
                verbose_print("filter:", pic2)
                skip = True
        # search for subdir to link to
        full_path = '(skipped)'
        while not linked and not skip:
            subdir = 'd' + str(dir_suffix) + '/' if dir_suffix > 0 else ''
            full_dir = dir_out + '/' + subdir
            if len(subdir) and not os.path.isdir(full_dir):
                os.mkdir(full_dir) # create subdirs as needed
            full_path = full_dir + base
            if os.path.isfile(full_path):
                dir_suffix += 1
                debug_print('dir_suffix =', dir_suffix)
            else:
                os.link(pic, full_path)
                linked = True
                verbose_print("linked:", full_path)
        debug_print('pic=%s, full_path=%s' % (pic, full_path))
    verbose_print('copy_tree: Succeeded')

#
# mainline
#

def main():
    global debug, verbose
    parser = argparse.ArgumentParser(
            description='Find pictures in a directory tree.')
    parser.add_argument('-d', '--debug', action='store_true',
            help='show debug output')
    parser.add_argument('-i', '--input', type=str, default='',
            help='input previous summary')
    parser.add_argument('-f', '--filter', type=str, default='',
            help='filter pictures in this directory')
    parser.add_argument('-l', '--link', type=str, default='',
            help='link pictures to new directory')
    parser.add_argument('-o', '--output', type=str, default='',
            help='output file summary')
    parser.add_argument('-v', '--verbose', action='store_true',
            help='show verbose output')
    parser.add_argument('directory', nargs='*',
            help='list of directories')
    args = parser.parse_args()
    debug   = args.debug
    verbose = args.verbose
    if debug:
        verbose = True

    # get source tree
    if args.input and len(args.directory):
        error_print('Cannot define both --input and directories.')
    if args.input:
        src_info = read_summary(args.input)
    else:
        if not len(args.directory):
            args.directory.append('.') # use current dir when no dirs
        pics = find_pics(args.directory)
        src_info = get_details(pics)
        find_duplicates(src_info)
        write_db(src_info, args.output)

    # get filter tree
    flt_info = {}
    if os.path.isfile(args.filter):
        flt_info = read_summary(args.filter)
    elif os.path.isdir(args.filter):
        pics = find_pics([args.filter])
        flt_info = get_details(pics)

    # create copy
    if os.path.isdir(args.link):
        copy_tree(src_info, flt_info, args.link)
    else:
        if len(args.link):
            error_print("Missing link dir:", args.link)

    # wrap up
    verbose_print("Succeeded")

if __name__ == "__main__":
    main()
    sys.exit(0)
