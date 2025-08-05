#! /usr/bin/env python3
'''
Use a data structure built by csv_delta_build.py to check what CSV entries are in the existing dataset,
and output a CSV of just the new and updated sequences,
as well as a copy of the input data structure but with matched entries removed (i.e., only containing unmatched entries).
'''

# imports
from gzip import open as gopen
from niemabf import HashSet
from os.path import isfile
from subprocess import run
from sys import argv, stderr, stdin, stdout
import argparse

# constants
STDIO = {'stderr':stderr, 'stdin':stdin, 'stdout':stdout}

# open file and return file object
def open_file(fn, mode='r', text=True):
    if fn in STDIO:
        return STDIO[fn]
    elif fn.lower().endswith('.gz'):
        if mode == 'a':
            raise NotImplementedError("Cannot append to gzip file")
        if text:
            mode += 't'
        return gopen(fn, mode)
    else:
        return open(fn, mode)

# parse user args
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-ic', '--input_csv', required=False, type=str, default='stdin', help="Input Dataset (CSV)")
    parser.add_argument('-is', '--input_structure', required=True, type=str, help="Input Structure (PKL)")
    parser.add_argument('-oc', '--output_csv', required=False, type=str, default='stdout', help="Output Dataset (CSV)")
    parser.add_argument('-os', '--output_structure', required=True, type=str, help="Output Structure (PKL)")
    args = parser.parse_args()
    for fn in [args.input_csv, args.input_structure]:
        if not isfile(fn) and fn not in STDIO and not fn.startswith('/dev/fd'):
            raise ValueError("File not found: %s" % fn)
    for fn in [args.output_csv, args.output_structure]:
        if isfile(fn):
            raise ValueError("File exists: %s" % fn)
    return args

# prune old entries from the input CSV
# Argument: `input_csv_file` = file stream of the input CSV file
# Argument: `input_structure` = data structure representing the CSV entries from the old CSV
# Argument: `output_csv_file` = file stream of the output pruned CSV file containing only new and updated entries
def prune_csv(input_csv_file, input_structure, output_csv_file):
    for line in input_csv_file:
        l = line.strip()
        if l in input_structure: # exists in data structure (so unchanged entry = prune)
            input_structure.remove(l)
        else: # doesn't exist in data structure (so new/updated entry or header line = include in output)
            output_csv_file.write(l + '\n')
    output_csv_file.flush()

# main program
def main():
    args = parse_args()
    structure = HashSet.load(args.input_structure)
    with open_file(args.input_csv, 'r') as input_csv_file:
        with open_file(args.output_csv, 'w') as output_csv_file:
            prune_csv(input_csv_file, structure, output_csv_file)
    structure.dump(args.output_structure)

# run main program
if __name__ == "__main__":
    main()
