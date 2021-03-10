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
# Test case for picscan
#

import filecmp
import os
import shutil
import subprocess
import sys

# variables

# constants
PROG = os.path.basename(sys.argv[0])
dir_in = "dir-in"
dir_out1 = "dir-out1"
dir_out2 = "dir-out2"
dir1 = dir_in + "/d1" # files that get linked to dir_out1
dir2 = dir_in + "/d2" # files to filter out
subd_key = 'subd'
name_key = 'name'
vals_key = 'vals'
num_vals = 1024 # 1K per letter
picscan_prog = 'picscan.py'
summary_file1 = 'dir-sum1'
summary_file2 = 'dir-sum2'

# global variables

# parameters
debug = True
verbose = True

# more complex test cases (full set after adding simple)
full_cases = [
    ##{name_key: 'file-or-dir', dupl_key: False, 'dir2': True},
]

# d1: expected in dir_out1
# d2: filter dir
# d3: pics to ignore
simple_cases = (
    # name,    subd,  vals
    ('file1.jpg', 1, 'abcd'),
    ('file2.jpg', 3, 'abcd'), # ignore because dup checksum
    ('file3.gif', 1, 'xyz'),
    ('file3.gif', 3, 'x'),    # ignore 2nd compressed file3
    ('file4.gif', 2, 'filt'), # ignore other file4
    ('file4.gif', 3, 'filt'),
)

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

# feature functions

def generate_file(full_name, vals):
    prog_print("generate_file:", full_name)
    dir = os.path.dirname(full_name)
    if not os.path.isdir(dir):
        os.mkdir(dir)
    with open(full_name, 'w') as pic:
        pic.write(vals * num_vals)

def file_compare(f1, f2):
    debug_print('file_compare(%s, %s)' % (f1, f2))
    equal = filecmp.cmp(f1, f2, shallow=True)
    if not equal:
        prog_print('Files differ: %s, %s' % (f1, f2))
    return equal

def files_for_case(case_dict):
    (name, subd, vals) = (
            case_dict[name_key], case_dict[subd_key], case_dict[vals_key])
    # uses dir1 when subd == 1
    generate_file(dir_in + '/d' + str(subd) + "/" + name, vals)

def create_files():
    # reset test dirs
    for dir in [dir_in, dir_out1, dir_out2]:
        shutil.rmtree(dir, ignore_errors=True)
        os.mkdir(dir)
    # handle all cases
    for case_dict in full_cases:
        files_for_case(case_dict)

# main functions

def run_test(args, indir):
    prog_print('Starting test...')
    create_files()
    commands = (
        './' + picscan_prog + " -d %s --filter '%s' --link '%s' %s" % (
            args, dir2, dir_out1, indir),
        "diff -r '%s' '%s'" % (dir1, dir_out1),
        # all pics should be filtered out, producing no links
        './' + picscan_prog + " -d -i %s --filter '%s' --link '%s'" % (
                summary_file1, summary_file1, dir_out2),
        "ls -lR '%s' '%s' '%s'" % (dir_in, dir_out1, dir_out2),
        )
    num_errors = 0
    for cmd in commands:
        prog_print("Command: %s" % (cmd,))
        err = subprocess.call(cmd, shell=True)
        if err != 0:
            num_errors += 1
    # TODO: read in summary
    # check results
    prog_print('Compare dirs: %s, %s' % (dir1, dir_out1))
    pics_in_dir1 = []
    for case_dict in full_cases:
        if case_dict[subd_key] == 1:
            pics_in_dir1.append(case_dict[name_key])
    pics_in_dir1.sort()
    # we know that dir_out1 is flat
    pics_in_out = os.listdir(dir_out1)
    pics_in_out.sort()
    if pics_in_dir1 == pics_in_out:
        diff_count = 0
        for pic in pics_in_dir1:
            debug_print('pic:', pic)
            f1 = os.path.join(dir1, pic)
            f2 = os.path.join(dir_out1, pic)
            if not file_compare(f1, f2):
                diff_count += 1
        if diff_count == 0:
            prog_print('All files the same.')
        num_errors += diff_count
    else:
        prog_print('Lists differ:', pics_in_dir1, pics_in_out)
        num_errors += 1
    # verify dir_out2 empty
    pics_in_out = os.listdir(dir_out2)
    if len(pics_in_out) > 0:
        prog_print('Dir must be empty:', dir_out2)
        num_errors += 1
    prog_print('Number of errors: %d' % (num_errors))
    return num_errors

def generate_cases():
    global full_cases
    for case_rec in simple_cases:
        case_dict = {
                name_key: case_rec[0],
                subd_key: case_rec[1],
                vals_key: case_rec[2]}
        full_cases.append(case_dict)
    verbose_print("Dump cases:", full_cases)

# main

def main():
    generate_cases()
    errs  = run_test('-o ' + summary_file1, dir_in)
    errs += run_test('-i ' + summary_file1, '')
    sys.exit(errs)

main()
sys.exit(0)
