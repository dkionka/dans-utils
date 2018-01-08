#!/usr/bin/env python3
#
# Copyright (c) 2018 Daniel P. Kionka; all rights reserved
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
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

#
# Test case for lnIdent
#

import os
import shutil
import subprocess
import sys

# variables

# constants
PROG = os.path.basename(sys.argv[0])
dir1 = "dir1"
dir2 = "dir2"
dir_list = (dir1, dir2)

# global variables

# more complex test cases (full set after adding simple)
full_cases = [
    {'name': 'file-or-dir', 'same': False, 'dir2': True},
]

# name, same, link1, link2
simple_cases = (
    ('same1',     True,  ),
    ('sub/same2', True,  ),
    ('same3',     True,  'diff1'),
    ('same4',     True,  '/tmp/qux'), # test fails because link does not exist
    ('diff1',     False, ),
    ('diff2',     False, '/tmp/foo', '/tmp/bar'),
)

# functions

def generate_file(full_name, link):
    # generate unique file - nanoseconds are always unique
    if link:
        subprocess.check_output("ln -s '%s' '%s'" % (link, full_name),
                shell=True)
    else:
        subprocess.check_output("date -Ins > '%s'" % (full_name, ), shell=True)

def duplicate_file(name):
    file1 = dir1 + "/" + name
    file2 = dir2 + "/" + name
    shutil.copyfile(file1, file2)

def files_for_case(case_dict):
    (name, same, link1, link2) = (
        case_dict['name'], case_dict['same'],
        case_dict.get('link1'), case_dict.get('link2'))
    print("%s: Creating: %s" % (PROG, name))
    subdir = os.path.dirname(name)
    for top_dir in dir_list:
        os.makedirs(top_dir + "/" + subdir, exist_ok=True)
        first = (top_dir == dir1) # first of 2 dirs in list
        if (first) or (not same) or (link1):
            link = link1 if (first) or (not link2) else link2
            generate_file(top_dir + "/" + name, link)
        else:
            duplicate_file(name)

def create_files():
    # reset test dirs
    shutil.rmtree(dir1, ignore_errors=True)
    shutil.rmtree(dir2, ignore_errors=True)
    os.mkdir(dir1)
    os.mkdir(dir2)
    # handle all cases
    for case_dict in full_cases:
        files_for_case(case_dict)

def run_test(ver, arg):
    print("\n%s: Starting test: ver=%s, arg=%s" % (PROG, ver, arg))
    create_files()
    commands = (
        "./lnIdent.%s -d %s '%s' '%s'" % (ver, arg, dir1, dir2),
        "diff -r '%s' '%s'" % (dir1, dir2), # same3 linked, but content differs
        "ls -lR '%s' '%s'" % (dir1, dir2))
    for cmd in commands:
        print("%s: Command: %s" % (PROG, cmd))
        subprocess.call(cmd, shell=True)
    # check results
    print("%s: Checking number of hard links..." % (PROG, ))
    num_errors = 0
    for case_dict in full_cases:
        # check all nlinks
        stat1 = os.lstat(dir1 + "/" + case_dict["name"])
        nlinks = stat1.st_nlink
        expected = 2 if case_dict["same"] else 1
        if nlinks != expected:
            print("%s: Links Error: %s: expected %d, have %d" %
                    (PROG, case_dict["name"], expected, nlinks))
            num_errors += 1
    print("%s: Number of link errors: %d\n" % (PROG, num_errors))

def generate_cases():
    global full_cases
    for case_rec in simple_cases:
        case_dict = {'name': case_rec[0], 'same': case_rec[1]}
        if len(case_rec) >= 3: case_dict['link1'] = case_rec[2]
        if len(case_rec) == 4: case_dict['link2'] = case_rec[3]
        full_cases.append(case_dict)
    print("Dump cases:", full_cases)

def main():
    generate_cases()
    run_test("py", "")
    run_test("py", "--ls")
    run_test("pl", "")

main()
sys.exit(0)
