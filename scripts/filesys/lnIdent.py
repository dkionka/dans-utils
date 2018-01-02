#!/usr/bin/env python3
#
# Copyright (c) 2006-2018 Daniel P. Kionka; all rights reserved
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
# lnIdent -- Recursively hard link identical files.
#
# This is a space-saver script.  When you have multiple source trees, you can
# run this to combine identical source files.
#
# This script finds all files in the first directory, looks for the same file
# in the second directory, compares them, and replaces the second file with a
# hard link to the first when they are identical.  It will reverse the link,
# replacing the first with the second, if the second one is older or already
# has hard links.
#
# Warning: If you about this script while it is creating the link, it may leave
# one of your files renamed with a ".lnIdent." prefix.
#
# TODO:
# - better analysis of where inodes are supported
#

import filecmp
import getopt
import os
import re
import shutil
import stat
import subprocess
import sys

# variables

# constants
useInoDev = True # (($^O ne "MSWin32") && ($^O ne "NetWare"))
useLsI = True # Unix or Cygwin
PROG = os.path.splitext(os.path.basename(sys.argv[0]))[0]
tmpPrefix = "." + PROG + "." + str(os.getpid()) + "."

# parameters
debug = False
quiet = False
verbose = False

# subroutines

def stripSlash(dir):
    """remove trailing slashes"""
    dir = re.sub(r'(.*[^/])/*$', r'\1', dir)
    return dir

def getLsI(file):
    # TODO: replace ls with function
    inode = str(subprocess.check_output("ls -i '" + file + "'", shell=True))
    inode = re.sub(r'\s.*', '', inode)
    if debug: print("getLsI(", file, "): ", inode)
    return inode

def areLinked(file1, file2, stat1, stat2):
    """See if already hard linked together"""
    if (useInoDev): # use Perl ino/dev
        if (not stat1.st_ino): warn("no inode for: $file1")
        if debug: print("inodes: "+str(stat1.st_ino)+", "+str(stat2.st_ino))
        if ((stat1.st_dev == stat2.st_dev) and (stat1.st_ino == stat2.st_ino)):
            return True
    elif (useLsI): # use ls -i
        inode1 = getLsI(file1)
        inode2 = getLsI(file2)
        if ((inode1) and (inode1 == inode2)):
            return True
    return False

def areIdentical(file1, file2, stat1, stat2):
    """See if same content"""

    # compare file modes (execute, writable)
    if ((os.access(file1, os.W_OK) != os.access(file2, os.W_OK)) or
        (os.access(file1, os.X_OK) != os.access(file2, os.X_OK))):
        return False

    # compare symlinks
    islnk1 = stat.S_ISLNK(stat1.st_mode)
    islnk2 = stat.S_ISLNK(stat2.st_mode)
    if (islnk1 or islnk2):
        if (islnk1 != islnk2): return False
        link1 = os.readlink(file1)
        link2 = os.readlink(file2)
        if debug: print("symlinks: " + link1 + ", " + link2)
        if (len("$link1$link2")):
            return (link1 == link2)

    # compare contents
    return (filecmp.cmp(file1, file2))

def linkFromTo(file1, file2):
    """Replace the second file with a hard link to the first."""
    if (not quiet): print("%s: %s -> %s" % (PROG, file1, file2))

    # move file2 to temp
    (dir2, base2) = os.path.split(file2)
    tmp2 = dir2 + "/" + tmpPrefix + base2
    full_tmp2 = shutil.move(file2, tmp2)
    if (not full_tmp2):
        if (not quiet): print("%s: Cannot rename: %s" % (PROG, file2))
        return
    if debug: print(file2, "->", tmp2)

    # link and clean up
    os.link(file1, file2)
    if (os.path.isfile(file2)):
        os.unlink(tmp2)
    else:
        if verbose: print("link failed! moving back")
        shutil.move(tmp2, file2) or die("Cannot restore: ", tmp2)

def walk_file(dir1, dir2, file1):
    """Called in os.walk loop."""
    # was wanted() for find in Perl version
    if debug: print("file1 = $file1")

    # strip off sub-path
    rest = file1.replace(dir1 + "/", "")
    if verbose: print("%s: Starting: %s" % (PROG, rest))

    # skip non-files
    if (not os.path.isfile(file1)):
        desc = ("directory" if os.path.isdir(file1) else "other")
        if verbose: print("%s: Skipping: %s" % (PROG, desc))
        return

    # does 2nd file exist?
    file2 = dir2 + "/" + rest
    if (not os.path.isfile(file2)):
        if verbose: print("missing:", file2)
        return

    # next tests need stat info
    stat1 = os.lstat(file1)
    stat2 = os.lstat(file2)
    if debug: print("file1=" + file1 +":\n", stat1)
    if debug: print("file2=" + file2 +":\n", stat2)
    # in case stat fails
    if ((not stat1) or (not stat2)):
        if verbose: print("stat error")
        return
    # skip if different sizes
    if (stat1.st_size != stat2.st_size):
        if verbose: print("different size")
        return
    if debug: print("same size")

    # skip if already hard linked together (same file)
    if (areLinked(file1, file2, stat1, stat2)):
        if verbose: print("already linked")
        return

    # several tests to see if same
    if (not areIdentical(file1, file2, stat1, stat2)):
        if verbose: print("not identical")
        return
    if verbose: print("identical!")

    # file identical -- which file to replace?

    # if one has hard links and the other does not, replace the lone file
    if ((stat1.st_nlink < 1) or (stat2.st_nlink < 1)): die("links")
    if (stat1.st_nlink == 1):
        if (stat2.st_nlink > 1):
            linkFromTo(file2, file1)
            return
    else:
        if (stat2.st_nlink == 1):
            linkFromTo(file1, file2)
            return

    # replace the older file
    if (stat1.st_mtime > stat2.st_mtime):
        linkFromTo(file2, file1)
    else:
        linkFromTo(file1, file2)

#
# mainline
#

def main():
    global debug, quiet, verbose
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                "dhqv", ["debug", "help", "quiet", "verbose"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    ok = True
    for o, a in opts:
        #print("o, a = ", o, a)
        if o in ("-d", "--debug"):
            debug = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-q", "--quiet"):
            quiet = True
        elif o in ("-v", "--verbose"):
            verbose = True
        else:
            ok = False
    if ((not ok) or (len(args) != 2)):
        assert False, "unhandled option"

    dir1 = stripSlash(args[0])
    dir2 = stripSlash(args[1])
    for dir in (dir1, dir2):
        if (not os.path.isdir(dir)):
            die("Bad directory: ", dir)

    for (root, dirs, files) in os.walk(dir1):
        for file in files:
            walk_file(dir1, dir2, root + "/" + file)

    if verbose: print(PROG + ": Succeeded")

main()
sys.exit(0)
