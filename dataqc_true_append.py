#! /usr/bin/env python3
'''
True Append for DataQC
'''

# imports
from csv import reader, writer
from datetime import datetime
from os.path import isfile
from shutil import copyfile
from subprocess import run
from sys import argv, stderr, stdin, stdout
import argparse

# constants
DATAQC_TRUE_APPEND_VERSION = '0.0.2'
STDIO = {'stderr':stderr, 'stdin':stdin, 'stdout':stdout}

# return the current time as a string
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# print to log (prefixed by current time)
def print_log(s='', end='\n'):
    print("[%s] %s" % (get_time(), s), file=stderr, end=end); stderr.flush()

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
    parser.add_argument('-c', '--csv-file', required=True, type=str, help="Input: User table (CSV)")
    parser.add_argument('-oc', '--old-csv-file', required=True, type=str, help="Input: Old table (CSV)")
    parser.add_argument('-of', '--old-fasta-file', required=True, type=str, help="Input: Old sequences (FASTA)")
    parser.add_argument('-or', '--old-full-report', required=True, type=str, help="Input: Old Full Report (CSV)")
    parser.add_argument('-f', '--fasta-file', required=True, type=str, help="Output: Updated sequences (FASTA)")
    parser.add_argument('-py', '--dataqc_py', required=True, type=str, help="PATH to DataQC.py script")
    parser.add_argument('-d', '--dram', required=False, type=str, default=None, help="DRAM CSV file")
    parser.add_argument('-C', '--comet', required=False, type=str, default=None, help="PATH to the COMET executable")
    parser.add_argument('-t', '--tn93', required=False, type=str, default=None, help="PATH to the TN93 executable")
    args = parser.parse_args()
    for fn in [args.csv_file, args.old_csv_file, args.old_fasta_file, args.old_full_report]:
        if not isfile(fn) and not fn.startswith('/dev/fd'):
            raise ValueError("File not found: %s" % fn)
    for fn in [args.fasta_file]:
        if fn.lower().endswith('.gz'):
            raise ValueError("Cannot directly write to gzip output file")
        if isfile(fn):
            raise ValueError("File exists: %s" % fn)
    return args

# parse input table
# Argument: `input_table` = path to input table CSV
# Return: `dict` in which keys are EHARS UIDs and values are clean_seqs
def parse_table(input_table_fn):
    # set things up
    header_row = None; col2ind = None; seqs = dict()
    infile = open_file(input_table_fn)

    # load sequences from table (and potentially write output FASTA)
    for row in reader(infile):
        # parse header row
        if header_row is None:
            header_row = row; col2ind = {k:i for i,k in enumerate(header_row)}
            for k in ['document_uid', 'predq_clean_seq']:
                if k not in col2ind:
                    raise ValueError("Column '%s' missing from input user table: %s" % (k, input_table_fn))

        # parse sequence row
        else:
            document_uid = row[col2ind['document_uid']].strip(); predq_clean_seq = row[col2ind['predq_clean_seq']].strip().upper()
            if document_uid in seqs:
                raise ValueError("Duplicate document UID (%s) in file: %s" % (document_uid, input_table_fn))
            seqs[document_uid] = predq_clean_seq

    # clean up and return
    infile.close()
    return seqs

# determine dataset deltas
# Argument: `seqs_new` = `dict` where keys are user-uploaded sequence IDs and values are sequences
# Argument: `seqs_old` = `dict` where keys are existing sequence IDs and values are sequences
# Return: `to_add` = `set` containing IDs in `seqs_new` that need to be added to `seqs_old`
# Return: `to_replace` = `set` containing IDs in `seqs_old` whose sequences need to be updated with those in `seqs_new`
# Return: `to_delete` = `set` containing IDs in `seqs_old` that need to be deleted
# Return: `to_keep` = `set` containing IDs in `seqs_old` that need to be kept as-is
def determine_deltas(seqs_new, seqs_old):
    to_add = set(); to_replace = set(); to_delete = set(seqs_old.keys()); to_keep = set()
    for ID in seqs_new:
        if ID in seqs_old:
            to_delete.remove(ID)
            if seqs_new[ID] == seqs_old[ID]:
                to_keep.add(ID)
            else:
                to_replace.add(ID)
        else:
            to_add.add(ID)
    return to_add, to_replace, to_delete, to_keep

# run DataQC on all new and updated sequences
# Argument: `user_csv_fn` = filename of user-given (new) CSV file
# Argument: `new_updated_csv_fn` = filename of the output CSV file containing only new/updated entries from the user-given (new) CSV file
# Argument: `to_add` = `set` containing IDs to add
# Argument: `to_replace` = `set` containing IDs whose sequences need to be updated
# Argument: `out_fasta_fn` = filename of output DataQC FASTA
# Argument: `dram_path` = path to DRAM CSV file
# Argument: `comet_path` = path to comet executable
# Argument: `tn93_path` = path to tn93 executable
def run_DataQC(user_csv_fn, new_updated_csv_fn, to_add, to_replace, out_fasta_fn, dataqc_py_path, dram_path=None, comet_path=None, tn93_path=None):
    # build CSV file containing just new/updated sequences
    new_updated_csv_file = open_file(new_updated_csv_fn, 'w')
    new_updated_csv_writer = writer(new_updated_csv_file)
    user_csv_file = open_file(user_csv_fn)
    document_uid_ind = None
    for row_num, row in enumerate(reader(user_csv_file)):
        if row_num == 0:
            for i, col in enumerate(row):
                if col.strip().lower() == 'document_uid':
                    document_uid_ind = i; break
            if document_uid_ind is None:
                raise ValueError("Column 'document_uid_ind' missing from input user table: %s" % user_csv_fn)
        document_uid = row[document_uid_ind].strip()
        if (row_num == 0) or (document_uid in to_add) or (document_uid in to_replace):
            new_updated_csv_writer.writerow(row)
    new_updated_csv_file.close(); user_csv_file.close()

    # run DataQC.py script on new/updated sequences
    dataqc_command = ['python3', dataqc_py_path, '--fasta-file', out_fasta_fn, '--csv-file', new_updated_csv_fn]
    if dram_path is not None:
        dataqc_command += ['--dram', dram_path]
    if comet_path is not None:
        dataqc_command += ['--comet', comet_path]
    if tn93_path is not None:
        dataqc_command += ['--tn93', tn93_path]
    log_f = open_file('%s.dataqc.log' % new_updated_csv_fn, 'w')
    print_log("Running DataQC: %s" % ' '.join(dataqc_command))
    run(dataqc_command, stderr=log_f); log_f.close()

# copy unchanged sequences to new/updated DataQC output
# assumes all lines (including empty ones) end in a newline character, so no newline == EOF
# Argument: `old_fasta_fn` = filename of old DataQC FASTA
# Argument: `to_keep` = `set` containing IDs to keep from old FASTA
# Argument: `out_fasta_fn` = filename of output DataQC FASTA
def copy_unchanged_seqs(old_fasta_fn, to_keep, out_fasta_fn):
    # set things up for reading/writing
    old_fasta_file = open_file(old_fasta_fn)
    out_fasta_file = open_file(out_fasta_fn, 'a')
    line = old_fasta_file.readline()

    # read old FASTA
    while True:
        # check for validity
        if len(line) == 0:
            break
        elif line[0] != '>':
            raise ValueError("Malformed FASTA: %s" % old_fasta_fn)
        document_uid = line.split('~')[0][1:].strip()

        # move to next sequence (and write this one to output if keeping it)
        keep_seq = document_uid in to_keep
        if keep_seq:
            out_fasta_file.write(line)
        line = old_fasta_file.readline()
        while len(line) != 0 and line[0] != '>':
            if keep_seq:
                out_fasta_file.write(line)
            line = old_fasta_file.readline()
    old_fasta_file.close(); out_fasta_file.close()

# copy unchanged entries to DataQC full report CSV
# Argument: `old_full_report_fn` = filename of old DataQC full report CSV
# Argument: `to_keep` = `set` containing IDs to keep from old full report CSV
# Argument: `out_full_report` = filename of output DataQC full report CSV
def copy_unchanged_full_report(old_full_report_fn, to_keep, out_full_report_fn):
    old_full_report_file = open_file(old_full_report_fn); out_full_report_file = open_file(out_full_report_fn, 'a')
    for line_num, line in enumerate(old_full_report_file):
        if line_num == 0:
            continue
        if line.split(',')[1].strip() in to_keep: # assumes document_uid is the second column (index 1 of the row)
            out_full_report_file.write(line)
    old_full_report_file.close(); out_full_report_file.close()

# main program
def main():
    print_log("Running DataQC True Append v%s" % DATAQC_TRUE_APPEND_VERSION)
    args = parse_args()
    print_log("Command: %s" % ' '.join(argv))
    print_log("Parsing user table: %s" % args.csv_file)
    seqs_new = parse_table(args.csv_file)
    print_log("- Num Sequences: %s" % len(seqs_new))
    print_log("Parsing old table: %s" % args.old_csv_file)
    seqs_old = parse_table(args.old_csv_file)
    print_log("- Num Sequences: %s" % (len(seqs_old)))
    print_log("Determining deltas between user table and old table...")
    to_add, to_replace, to_delete, to_keep = determine_deltas(seqs_new, seqs_old)
    print_log("- Add: %s" % len(to_add))
    print_log("- Replace: %s" % len(to_replace))
    print_log("- Delete: %s" % len(to_delete))
    print_log("- Do nothing: %s" % (len(to_keep)))
    new_updated_csv_fn = '%s.new_updated.csv' % args.csv_file.rstrip('.csv')
    print_log("Performing new DataQC analyses and writing FASTA output to: %s" % args.fasta_file)
    run_DataQC(args.csv_file, new_updated_csv_fn, to_add, to_replace, args.fasta_file, args.dataqc_py, dram_path=args.dram, comet_path=args.comet, tn93_path=args.tn93)
    print_log("Copying unchanged DataQC sequences from: %s" % args.old_fasta_file)
    copy_unchanged_seqs(args.old_fasta_file, to_keep, args.fasta_file)
    out_full_report_fn = '%s.full_report.csv' % '.'.join(args.fasta_file.split('.')[:-1])
    print_log("Copying new DataQC full report contents to: %s" % out_full_report_fn)
    copyfile('%s.full_report.csv' % new_updated_csv_fn.rstrip('.csv'), out_full_report_fn)
    print_log("Copying unchanged DataQC full report entries from: %s" % args.old_full_report)
    copy_unchanged_full_report(args.old_full_report, to_keep, out_full_report_fn)

# run main program
if __name__ == "__main__":
    main()
