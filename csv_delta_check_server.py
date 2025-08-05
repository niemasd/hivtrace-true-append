#! /usr/bin/env python3
'''
Use a data structure built by csv_delta_check_client.py to check what CSV entries were removed from the old dataset
'''

# imports
from gzip import open as gopen
from niemabf import HashSet
from os.path import isfile
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
    parser.add_argument('-ic', '--input_csv', required=False, type=str, default='stdin', help="Input Old Dataset (CSV)")
    parser.add_argument('-is', '--input_structure', required=True, type=str, help="Input Pruned Structure (PKL)")
    parser.add_argument('-o', '--output_csv', required=False, type=str, default='stdout', help="Output Removed Entries (CSV)")
    args = parser.parse_args()
    for fn in [args.input_csv, args.input_structure]:
        if not isfile(fn) and fn not in STDIO and not fn.startswith('/dev/fd'):
            raise ValueError("File not found: %s" % fn)
    if isfile(args.output_csv):
        raise ValueError("File exists: %s" % args.output_csv)
    return args

# determine which sequences were removed from the old CSV file
# Argument: `input_csv_file` = file stream of the input CSV file
# Argument: `input_structure` = data structure representing the pruned CSV entries from the old CSV (representing elements that were removed)
# Return: `removed` = `set` containing the entries that were removed from the old CSV file
def determine_removed(input_csv_file, input_structure):
    removed = set()
    for line in input_csv_file:
        l = line.strip()
        if l in input_structure: # exists in pruned data structure (so removed entry)
            removed.add(l)
    return removed

# main program
def main():
    args = parse_args()
    structure = HashSet.load(args.input_structure)
    with open_file(args.input_csv, 'r') as input_csv_file:
        removed = determine_removed(input_csv_file, structure)
    with open_file(args.output_csv, 'w') as output_csv_file:
        for entry in removed:
            output_csv_file.write(entry + '\n')

# run main program
if __name__ == "__main__":
    main()
