#!/usr/bin/python
#    This is a component of emc2
#    Copyright 2015 Michael Brown <producer@holotronic.dk>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import sys
import commands
import re
import sys

from sets import Set

outputlines = set()
linelistset = set()
linenumber = 0
funcname = ""
labellist = []
source = ""

def buf_input():
    global linenumber, funcname, source
    if len(sys.argv) <= 2:
        print (" Please input name of halfile or - for stdin and ")
        print (" name of output function to extract")
        exit(0)
    else:
        if sys.argv[1] == '-':
            source = sys.stdin.readlines()
        else:
            source = open(sys.argv[1])
        funcname = sys.argv[2]
        linenumber = 0

def input():
    global linenumber,source
    linenumber = 0
    if sys.argv[1] != '-':
        source = open(sys.argv[1])

    for line in source:
        linenumber += 1	
        yield line

def find_func_label():
    for line in input():
        has_mach = line.find(funcname)
        if has_mach >= 0:
            words = line.split()
            outputlines.add(line)
            linelistset.add(linenumber)
            return words[0]

def find_label(label):
    global labellist, lline
    for line in input():
        has_mach = line.find(label)
        if has_mach >= 0:
            words = line.split()
            outputlines.add(line)
            linelistset.add(linenumber)
            lline = linenumber
            labellist.append(words[0])

def add_label(label):
    global outputlines
    for line in input():
        has_mach = line.find(label)
        if has_mach >= 0:
            words = line.split()
            outputlines.add(line)
            linelistset.add(linenumber)

def print_line(num):
    for line in input():
        if linenumber == num:
            print ("%s" % (line.rstrip('\n')))                     

buf_input()
func_label = find_func_label()

find_label(func_label)

while len(labellist) > 0:
    add_label(labellist.pop())

print ("digraph net {")
print ("    node [shape=record];")

linelist = sorted(list(linelistset))
for index in range(len(linelist)):
    print_line(linelist[index])

print ("}")
