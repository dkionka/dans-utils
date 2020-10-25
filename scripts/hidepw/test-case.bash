#!/bin/bash -epux

# tests for hidepw.py

# simple output checks
./hidepw.py password | grep -q 'p a s s w o r d'
./hidepw.py -c 8 password | grep -q '^p a s s w o r d'
./hidepw.py -s , password | grep -q 'p,a,s,s,w,o,r,d'
./hidepw.py -u Password | grep -q 'P a s s w o r d'

# check character range
./hidepw.py Password 2>&1 | grep -q Invalid

# check fitting
./hidepw.py -r 3 -c 3 aaa bbb ccc | grep -q 'a a a'
./hidepw.py -r 3 -c 3 aaa bbb ccc ddd 2>&1 | grep -q 'Cannot'

echo $0: Succeeded
