#!/usr/bin/env perl
#
# $Header: /cvsroot-fuse/gdbi/src/build/lnIdent.pl,v 1.3 2007/08/17 23:43:42 dkionka Exp $
#
# Copyright (c) 2006-2016 Daniel P. Kionka; all rights reserved
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

use strict;
use warnings;

use Data::Dumper;
use File::Basename;
use File::Compare;
use File::Find;
use File::stat;
use Getopt::Long;

# variables

# constants
my $useInoDev = (($^O ne "MSWin32") && ($^O ne "NetWare"));
my $useLsI = 1;                         # Unix or Cygwin
my $PROG = basename($0, ".pl");
my $tmpPrefix = ".$PROG.$$.";

# parameters
# TODO: add getopt
my $debug = 0;
my $quiet = 0;
my $verbose = 0;

# must be global for wanted()
my ($dir1, $dir2);

# subroutines

sub stripSlash($)
{
    my ($dir) = @_;
    # remove trailing slashes
    $dir =~ s,(.*[^/])/*$,$1,;
    return $dir;
}

sub getLsI($)
{
    my ($file) = @_;
    my $inode = `ls -i "$file"`;
    chomp($inode);
    $inode =~ s/\s.*//;
    print "getLsI($file): $inode\n" if ($debug);
    return $inode;
}

# see if already hard linked together
sub areLinked($$$$)
{
    my ($file1, $file2, $stat1, $stat2) = @_;

    if ($useInoDev) {                   # use Perl ino/dev
        warn "no inode for: $file1" if (! $stat1->ino);
        print "inodes: ", $stat1->ino, ", ", $stat2->ino, "\n" if ($debug);
        return 1 if (($stat1->dev == $stat2->dev) &&
                   ($stat1->ino == $stat2->ino));
    }
    elsif ($useLsI) {                   # use ls -i
        my $inode1 = getLsI($file1);
        my $inode2 = getLsI($file2);
        return 1 if (($inode1) && ($inode1 eq $inode2));
    }
    return 0;
}

# see if same content
sub areIdentical($$)
{
    my ($file1, $file2) = @_;

    # compare file modes (execute, writable)
    return 0 if (((-x $file1) * 2 + (-w $file1) * 4) != ((-x $file2) * 2 + (-w $file2) * 4));

    # compare symlinks
    my $link1 = readlink($file1);
    my $link2 = readlink($file2);
    if (defined($link1) || defined($link2)) {
        print "symlinks: $link1,$link2\n" if ($debug);
        return 0 if (! (defined($link1) && defined($link2)));
        if (length("$link1$link2")) {
            return ($link1 eq $link2);
        }
    }

    # compare contents
    return (! compare($file1, $file2));
}

# replace the second file with a hard link to the first
sub linkFromTo($$)
{
    my ($file1, $file2) = @_;
    print "$PROG: $file1 -> $file2\n" if (! $quiet);

    # move file2 to temp
    my ($base2, $dir2, undef) = fileparse($file2);
    my $tmp2 = "$dir2$tmpPrefix$base2";
    return if (! rename($file2, $tmp2));
    print "file2 -> $tmp2\n" if ($debug);

    # link and clean up
    my $ok = link($file1, $file2);
    if ($ok) {
        unlink($tmp2) || die "Cannot unlink: $tmp2";
    }
    else {
        print "link failed! moving back\n" if ($debug);
        rename($tmp2, $file2) || die "Cannot restore: $tmp2";
    }
}

# called by find
sub wanted()
{
    my $file1 = $_;
    print "file1 = $file1\n" if ($debug);

    # strip off sub-path
    my ($rest) = ($File::Find::name =~ m,$dir1/(.*),);
    return if (! defined($rest));
    print "$PROG: $rest: " if ($verbose);

    # skip non-files
    if (! -f $file1) {
        my $desc = ((-d $file1) ? "directory" : "other");
        print "$desc\n" if ($verbose);
        return;
    }

    # does 2nd file exist?
    my $file2 = "$dir2/$rest";
    if (! -f $file2) {
        print "missing\n" if ($verbose);
        return;
    }
    print "file2 = $file2\n" if ($debug);

    # next tests need stat info
    my $stat1 = lstat($file1);
    my $stat2 = lstat($file2);
    print "file1:\n", Dumper($stat1) if ($debug);
    print "file2:\n", Dumper($stat2) if ($debug);
    # in case stat fails
    if ((! $stat1) || (! $stat2)) {
        print "error\n" if ($verbose);
        return;
    }
    # skip if different sizes
    if ($stat1->size != $stat2->size) {
        print "different\n" if ($verbose);
        return;
    }
    print "same size\n" if ($debug);

    # skip if already hard linked together (same file)
    if (areLinked($file1, $file2, $stat1, $stat2)) {
        print "linked\n" if ($verbose);
        return;
    }

    # several tests to see if same
    if (! areIdentical($file1, $file2)) {
        print "different\n" if ($verbose);
        return;
    }
    print "identical!\n" if ($verbose);

    # file identical -- which file to replace?

    # if one has hard links and the other does not, replace the lone file
    die "links" if (($stat1->nlink < 1) || ($stat2->nlink < 1));
    if ($stat1->nlink == 1) {
        if ($stat2->nlink > 1) {
            linkFromTo($file2, $file1);
            return;
        }
    }
    else {
        if ($stat2->nlink == 1) {
            linkFromTo($file1, $file2);
            return;
        }
    }

    # replace the older file
    if ($stat1->mtime > $stat2->mtime) {
        linkFromTo($file2, $file1);
    }
    else {
        linkFromTo($file1, $file2);
    }
}

#
# mainline
#

my $ok = GetOptions(
    debug   => \$debug,
    quiet   => \$quiet,
    verbose => \$verbose);
die "usage" if ((! $ok) || (@ARGV != 2));

$dir1 = stripSlash($ARGV[0]);
$dir2 = stripSlash($ARGV[1]);
foreach my $dir ($dir1, $dir2) {
    die "Bad directory: $dir" if (! -d $dir);
}

find({wanted=>\&wanted, no_chdir=>1}, $dir1);

print "$PROG: Succeeded\n" if ($verbose);
exit 0;
