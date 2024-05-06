#! /usr/bin/env python3
'''
True Append for HIV-TRACE
'''

# imports
from csv import reader
from datetime import datetime
from gzip import open as gopen
from os.path import isfile
from subprocess import run
from sys import argv, stderr
import argparse

# constants
VERSION = '0.0.1'
DEFAULT_TN93_ARGS = ''
DEFAULT_TN93_PATH = 'tn93'

# return the current time as a string
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# print to log (prefixed by current time)
def print_log(s='', end='\n'):
    print("[%s] %s" % (get_time(), s), file=stderr, end=end); stderr.flush()

# parse user args
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-it', '--input_user_table', required=True, type=str, help="Input: User table (CSV)")
    parser.add_argument('-iT', '--input_old_table', required=True, type=str, help="Input: Old table (CSV)")
    parser.add_argument('-iD', '--input_old_dists', required=True, type=str, help="Input: Old TN93 distances (CSV)")
    parser.add_argument('-oD', '--output_dists', required=True, type=str, help="Output: Updated TN93 distances (CSV)")
    parser.add_argument('--tn93_args', required=False, type=str, default=DEFAULT_TN93_ARGS, help="Optional tn93 arguments")
    parser.add_argument('--tn93_path', required=False, type=str, default=DEFAULT_TN93_PATH, help="Path to tn93 executable")
    args = parser.parse_args()
    for fn in [args.input_user_table, args.input_old_table, args.input_old_dists]:
        if not isfile(fn):
            raise ValueError("File not found: %s" % fn)
    return args

# parse input table
# Argument: `input_table` = path to input table CSV
# Return: `dict` in which keys are EHARS UIDs and values are clean_seqs
def parse_table(input_table):
    # set things up
    header_row = None; col2ind = None; seqs = dict()
    if input_table.lower().endswith('.gz'):
        infile = gopen(input_table, 'rt')
    else:
        infile = open(input_table, 'r')

    # load sequences from table (and potentially write output FASTA)
    for row in reader(infile):
        # parse header row
        if header_row is None:
            header_row = row; col2ind = {k:i for i,k in enumerate(header_row)}
            for k in ['ehars_uid', 'clean_seq']:
                if k not in col2ind:
                    raise ValueError("Column '%s' missing from input user table: %s" % (k, input_user_table))

        # parse sequence row
        else:
            ehars_uid = row[col2ind['ehars_uid']].strip(); clean_seq = row[col2ind['clean_seq']].strip().upper()
            if ehars_uid in seqs:
                raise ValueError("Duplicate EHARS UID (%s) in file: %s" % (ehars_uid, input_table))
            seqs[ehars_uid] = clean_seq

    # clean up and return
    infile.close()
    return seqs

# run tn93 on all pairs in one dataset
# Argument: `seqs` = `dict` where keys are sequence IDs and values are sequences
# Argument: `tn93_args` = string containing optional tn93 arguments
# Argument: `tn93_path` = path to tn93 executable
def run_tn93_all_pairs(seqs, tn93_args=DEFAULT_TN93_ARGS, tn93_path=DEFAULT_TN93_PATH):
    tn93_command = [tn93_path] + [v.strip() for v in tn93_args.split()]
    fasta_data = ''.join('>%s\n%s\n' % kv for kv in seqs.items()).encode('utf-8')
    tmp = run(tn93_command, input=fasta_data, capture_output=True)
    #print(tmp)
    pass # TODO

# main program
def main():
    print_log("Running HIV-TRACE True Append v%s" % VERSION)
    args = parse_args()
    print_log("Command: %s" % ' '.join(argv))
    print_log("Parsing user table: %s" % args.input_user_table)
    seqs_user = parse_table(args.input_user_table)
    print_log("Parsing old table: %s" % args.input_old_table)
    seqs_old = parse_table(args.input_old_table)
    run_tn93_all_pairs(seqs_user, tn93_args=args.tn93_args, tn93_path=args.tn93_path)

# run main program
if __name__ == "__main__":
    main()
