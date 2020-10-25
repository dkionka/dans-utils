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
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

#
# hidepw -- Hide passwords in a matrix of random characters.
#
# TODO:
# - allow punctuation
#

import argparse
import getopt
import random
import os
import sys

# variables

# constants
PROG = os.path.basename(sys.argv[0])

# parameters
debug = False
verbose = False

# classes

class GenCharacter:
    def __init__(self, upper=False):
        self.upper = upper

    def get_random(self):
        while True:
            num = random.randint(ord(" ")+1, ord("~"))
            char = chr(num)
            if char.isdigit() or char.islower():
                return char
            if self.upper and char.isupper():
                return char

# subroutines

def debug_print(*args):
    if debug:
        print(*args)
        sys.stdout.flush()

def verbose_print(*args):
    if verbose:
        print(PROG + ":", end=" ")
        print(*args)
        sys.stdout.flush()

def gen_matrix(gen_char, width, height, spacing, passwords):
    debug_print("width=%s, height=%s, spacing=%s" % (width, height, spacing))

    # generate matrix
    matrix = []
    used = []
    for y in range(height):
        row = []
        urow = []
        for x in range(width):
            row.append(gen_char.get_random())
            urow.append(False)
        matrix.append(row)
        used.append(urow)

    # insert passwords
    for pw in passwords:
        plen = len(pw)
        verbose_print("Insert password: %s, len=%d" % (pw, plen))
        if plen == 0 or plen > width:
            sys.exit("Password too long: " + pw)
        looking = True
        while looking:
            # find place to put it
            startx = random.randint(0, width - plen)
            starty = random.randint(0, height - 1)
            debug_print("startx=%s, starty=%s" % (startx, starty))
            collision = False
            for x in range(plen):
                if used[starty][startx + x]:
                    collision = True
            # add if no collision
            if not collision:
                looking = False
                for x in range(plen):
                    matrix[starty][startx + x] = pw[x]
                    used[starty][startx + x] = True

    # print matrix
    for y in range(height):
        str = ""
        for x in range(width):
            if len(str) > 0:
                str += spacing
            str += matrix[y][x]
        print(str)


#
# mainline
#

def main():
    global debug, verbose
    parser = argparse.ArgumentParser(
            add_help=False, # want -h for height
            description='Hide passwords in a matrix of random characters.')
    parser.add_argument('-d', '--debug', action='store_true',
            help='show debug output')
    parser.add_argument('-h', '--height', type=int, default=10,
            help='height of matrix')
    parser.add_argument('-s', '--spacing', type=str, default=' ',
            help='spacing between characters ("," for spreadsheet)')
    parser.add_argument('-u', '--upper', action='store_true',
            help='include upper case')
    parser.add_argument('-v', '--verbose', action='store_true',
            help='show verbose output')
    parser.add_argument('-w', '--width', type=int, default=20,
            help='width of matrix')
    parser.add_argument('passwords', nargs='*',
            help='password')
    args = parser.parse_args()
    debug   = args.debug
    verbose = args.verbose
    if debug:
        verbose = True

    # read passwords from stdin when not on command line
    if len(args.passwords) == 0:
        verbose_print("Enter passwords:")
        for line in sys.stdin:
            line = line.strip()
            if len(line) == 0:
                break
            args.passwords.append(line)

    gen_char = GenCharacter(args.upper)

    gen_matrix(gen_char, args.width, args.height, args.spacing, args.passwords)

    verbose_print("Succeeded")

main()
sys.exit(0)
