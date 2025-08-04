#! /usr/bin/env python3
'''
Build a data structure to store what CSV entries are in the existing dataset
'''

# imports
from gzip import open as gopen
from os.path import isfile
from niemabf import HashSet
from subprocess import run
from sys import argv, stderr, stdin, stdout
import argparse

# constants
HASH_FUNC = 'sha512_str'
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
    parser.add_argument('-i', '--input_csv', required=False, type=str, default='stdin', help="Input Dataset (CSV)")
    parser.add_argument('-o', '--output_structure', required=True, type=str, help="Output Structure (PKL)")
    args = parser.parse_args()
    if not isfile(args.input_csv) and args.input_csv not in STDIO and not args.input_csv.startswith('/dev/fd'):
        raise ValueError("File not found: %s" % args.input_csv)
    if isfile(args.output_structure):
        raise ValueError("File exists: %s" % args.output_structure)
    return args

# build the data structure from a CSV
# Argument: `csv_file` = file stream of the input CSV file
# Return: `output_structure` = data structure representing the CSV entries from `csv_file`
def build_data_structure(csv_file, hash_func=HASH_FUNC):
    output_structure = HashSet()
    for line in csv_file:
        if 'ehars_uid' not in line: # skip header row
            output_structure.insert(line.strip())
    return output_structure

# main program
def main():
    args = parse_args()
    with open_file(args.input_csv, 'r') as csv_file:
        output_structure = build_data_structure(csv_file, hash_func=HASH_FUNC)
    output_structure.dump(args.output_structure)

# run main program
if __name__ == "__main__":
    main()
