#! /usr/bin/env python3
'''
True Append for HIV-TRACE
'''

# imports
from csv import reader
from datetime import datetime
from gzip import open as gopen
from os.path import isfile
from sys import argv, stderr
import argparse

# constants
VERSION = '0.0.1'

# return the current time as a string
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# print to log (prefixed by current time)
def print_log(s='', end='\n'):
    print("[%s] %s" % (get_time(), s), file=stderr, end=end); stderr.flush()

# parse user args
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-t', '--input_user_table', required=True, type=str, help="Input: User table (CSV)")
    parser.add_argument('-T', '--input_old_table', required=True, type=str, help="Input: Old table (CSV)")
    parser.add_argument('-D', '--input_old_dists', required=True, type=str, help="Input: Old TN93 distances (CSV)")
    parser.add_argument('-f', '--output_user_fasta', required=True, type=str, help="Output: User sequences (FASTA)")
    parser.add_argument('-F', '--output_old_fasta', required=True, type=str, help="Output: Old sequences (FASTA)")
    parser.add_argument('--overwrite_output_user_fasta', action="store_true", help="Overwrite output user sequences FASTA")
    parser.add_argument('--overwrite_output_old_fasta', action="store_true", help="Overwrite output old sequences FASTA")
    parser.add_argument('--tn93_args', required=False, type=str, default='', help="Optional tn93 arguments")
    parser.add_argument('--tn93_path', required=False, type=str, default='tn93', help="Path to tn93 executable")
    args = parser.parse_args()
    for fn in [args.input_user_table, args.input_old_table, args.input_old_dists]:
        if not isfile(fn):
            raise ValueError("File not found: %s" % fn)
    return args

# parse input table
# Argument: `input_table` = path to input table CSV
# Argument: `output_fasta` = path to output FASTA
# Argument: `overwrite_output_fasta` = boolean to overwrite `output_fasta` if it exists (not overwriting = faster)
# Return: `dict` in which keys are EHARS UIDs and values are clean_seqs
def parse_table(input_table, output_fasta, overwrite_output_fasta=True):
    # set things up
    header_row = None; col2ind = None; seqs = dict()
    if input_table.lower().endswith('.gz'):
        infile = gopen(input_table, 'rt')
    else:
        infile = open(input_table, 'r')
    if isfile(output_fasta) and not overwrite_output_fasta:
        outfile_fasta = None # skip writing output FASTA if it already exists (e.g. for speed)
    elif output_fasta.lower().endswith('.gz'):
        outfile_fasta = gopen(output_fasta, 'wt', compresslevel=9)
    else:
        outfile_fasta = open(output_fasta, 'w')

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

            # write sequence to FASTA (if applicable)
            if outfile_fasta is not None:
                outfile_fasta.write('>%s\n%s\n' % (ehars_uid, clean_seq))

    # clean up and return
    infile.close()
    if outfile_fasta is not None:
        outfile_fasta.close()
    return seqs

# main program
def main():
    print_log("Running HIV-TRACE True Append v%s" % VERSION)
    args = parse_args()
    print_log("Command: %s" % ' '.join(argv))
    print_log("Parsing user table...")
    print_log("- Input user table CSV: %s" % args.input_user_table)
    print_log("- Output user FASTA: %s" % args.output_user_fasta)
    print_log("- %s if output exists" % {True:"OVERWRITE", False:"DO NOT overwrite"}[args.overwrite_output_user_fasta])
    seqs_user = parse_table(args.input_user_table, args.output_user_fasta, overwrite_output_fasta=args.overwrite_output_user_fasta)
    print_log("Parsing old table...")
    print_log("- Input old table CSV: %s" % args.input_old_table)
    print_log("- Output old FASTA: %s" % args.output_old_fasta)
    print_log("- %s if output exists" % {True:"OVERWRITE", False:"DO NOT overwrite"}[args.overwrite_output_old_fasta])
    seqs_old = parse_table(args.input_old_table, args.output_old_fasta, overwrite_output_fasta=args.overwrite_output_old_fasta)

# run main program
if __name__ == "__main__":
    main()
