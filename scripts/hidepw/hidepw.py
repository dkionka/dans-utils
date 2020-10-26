#!/usr/bin/env python3
#
# Copyright (c) 2020 Daniel P. Kionka; all rights reserved
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
# hidepw -- Hide passwords in a matrix of random characters.
#
# TODO:
# - add vertical strings
# - add seed for test cases and documentation
#

import argparse
import getopt
import random
import os
import string
import sys

# variables

# constants
PROG = os.path.basename(sys.argv[0])

# parameters
debug = False
verbose = False

# classes

class GenCharacter:
    def __init__(self,
            lower=True, numbers=False, punctuation=False, upper=False):
        self.lower       = lower
        self.numbers     = numbers
        self.punctuation = punctuation
        self.upper       = upper
        if not lower and not numbers and not punctuation and not upper:
            sys.exit(PROG + ": no characters are enabled")

    def is_legal(self, char):
        if self.lower and char.islower():
            return True
        if self.numbers and char.isdigit():
            return True
        if self.punctuation and char in string.punctuation:
            return True
        if self.upper and char.isupper():
            return True
        return False

    def get_random(self):
        while True:
            num = random.randint(ord(" ")+1, ord("~"))
            char = chr(num)
            if self.is_legal(char):
                return char
            debug_print("skip random: num=%d, char=%s" % (num, char))

# subroutines

def debug_print(*args):
    if debug:
        print(*args)
        sys.stderr.flush()

def prog_print(*args):
    print(PROG + ":", end=" ", file=sys.stderr)
    print(*args, file=sys.stderr)
    sys.stderr.flush()

def verbose_print(*args):
    if verbose:
        prog_print(*args)

def gen_matrix(gen_char, cols, rows, spacing, passwords):
    debug_print("cols=%s, rows=%s, spacing=%s" % (cols, rows, spacing))

    # generate matrix
    matrix = []
    used = []
    for y in range(rows):
        row = []
        urow = []
        for x in range(cols):
            row.append(gen_char.get_random())
            urow.append(False)
        matrix.append(row)
        used.append(urow)

    # insert passwords
    for pw in passwords:
        plen = len(pw)
        verbose_print("Insert password: %s, len=%d" % (pw, plen))
        if plen < 1 or plen > cols:
            sys.exit(PROG + ": Password too long: " + pw)
        looking = True
        for count in range(100):
            # find place to put it
            startx = random.randint(0, cols - plen)
            starty = random.randint(0, rows - 1)
            debug_print("startx=%d, starty=%d" % (startx, starty))
            collision = False
            for x in range(plen):
                if used[starty][startx + x]:
                    debug_print("collision: count=%d, x=%d" % (count, x))
                    collision = True
            if collision:
                continue
            # add if no collision
            looking = False
            invalid = ""
            for x in range(plen):
                if not gen_char.is_legal(pw[x]):
                    invalid += pw[x]
                matrix[starty][startx + x] = pw[x]
                used[starty][startx + x] = True
            if len(invalid):
                prog_print("Invalid characters in password, %s: %s" %
                        (pw, invalid))
            break
        if looking:
            sys.exit(PROG + ": Cannot fit password: " + pw)

    # print matrix
    for y in range(rows):
        str = ""
        for x in range(cols):
            if len(str):
                str += spacing
            str += matrix[y][x]
        print(str)


#
# mainline
#

def main():
    global debug, verbose
    lower = True
    parser = argparse.ArgumentParser(
            description='Hide passwords in a matrix of random characters.')
    parser.add_argument('-a', '--all', action='store_true',
            help='include all characters')
    parser.add_argument('-c', '--columns', type=int, default=40,
            help='columns of matrix')
    parser.add_argument('-d', '--debug', action='store_true',
            help='show debug output')
    parser.add_argument('-n', '--numbers', action='store_true',
            help='include numbers')
    parser.add_argument('--no-lower', action='store_true',
            help='exclude lowercase letters')
    parser.add_argument('-p', '--punctuation', action='store_true',
            help='include punctuation')
    parser.add_argument('-r', '--rows', type=int, default=20,
            help='rows of matrix')
    parser.add_argument('-s', '--spacing', type=str, default=' ',
            help='spacing between characters ("," for spreadsheet)')
    parser.add_argument('-u', '--upper', action='store_true',
            help='include upper case')
    parser.add_argument('-v', '--verbose', action='store_true',
            help='show verbose output')
    parser.add_argument('password', nargs='*',
            help='list of passwords')
    args = parser.parse_args()
    debug   = args.debug
    verbose = args.verbose
    debug_print("args = ", args)
    if debug:
        verbose = True

    # read passwords from stdin when not on command line
    if not len(args.password):
        verbose_print("Enter passwords, blank line to end:")
        for line in sys.stdin:
            line = line.strip()
            if not len(line):
                break
            args.password.append(line)

    if args.all:
        args.numbers     = True
        args.punctuation = True
        args.upper       = True
        lower            = True
    if args.no_lower:
        lower = False
    gen_char = GenCharacter(lower, args.numbers, args.punctuation, args.upper)

    gen_matrix(gen_char, args.columns, args.rows, args.spacing, args.password)

    verbose_print("Succeeded")

if __name__ == "__main__":
    main()
    sys.exit(0)
