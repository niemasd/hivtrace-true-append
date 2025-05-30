#! /usr/bin/env python3
'''
True Append for cawlign
'''

# imports
from datetime import datetime
from gzip import open as gopen
from os.path import isfile
from subprocess import run
from sys import argv, stderr, stdin, stdout
import argparse

# constants
CAWLIGN_TRUE_APPEND_VERSION = '0.0.1'
DEFAULT_CAWLIGN_PATH = 'cawlign'
DEFAULT_CAWLIGN_ARGS = ''
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
    parser.add_argument('-of', '--old_unaligned_file', required=True, type=str, help="Input: Old unaligned sequences (FASTA)")
    parser.add_argument('-oa', '--old_aligned_file', required=True, type=str, help="Input: Old aligned sequences (FASTA)")
    parser.add_argument('-o', '--output_aligned_file', required=False, type=str, default='stdout', help="Output: Aligned sequences (FASTA)")
    parser.add_argument('--cawlign_args', required=False, type=str, default=DEFAULT_CAWLIGN_ARGS, help="Optional cawlign arguments")
    parser.add_argument('--cawlign_path', required=False, type=str, default=DEFAULT_CAWLIGN_PATH, help="Path to the cawlign executable")
    parser.add_argument('fasta_file', nargs='?', type=str, default='stdin', help="Input: User unaligned sequences (FASTA)")
    args = parser.parse_args()
    for fn in [args.old_unaligned_file, args.old_aligned_file, args.fasta_file]:
        if not isfile(fn) and fn not in STDIO and not fn.startswith('/dev/fd'):
            raise ValueError("File not found: %s" % fn)
    for fn in [args.output_aligned_file]:
        if fn.lower().endswith('.gz'):
            raise ValueError("Cannot directly write to gzip output file. To gzip the output, specify 'stdout' as the output file, and then pipe to gzip.")
        if isfile(fn):
            raise ValueError("File exists: %s" % fn)
    return args

# load FASTA
def load_fasta(fn):
    infile = open_file(fn); seqs = dict(); name = None; seq = ''
    for line in infile:
        l = line.strip()
        if len(l) == 0:
            continue
        if l[0] == '>':
            if name is not None:
                if len(seq) == 0:
                    raise ValueError("Malformed FASTA: %s" % fn)
                seqs[name] = seq
            name = l[1:]
            if name in seqs:
                raise ValueError("Duplicate sequence ID (%s): %s" % (name, fn))
            seq = ''
        else:
            seq += l
    if name is None or len(seq) == 0:
        raise ValueError("Malformed FASTA: %s" % fn)
    seqs[name] = seq; infile.close()
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

# copy alignments from unchanged sequences
def copy_unchanged_alignments(to_keep, aln_old, out_aln_file):
    for k in to_keep:
        out_aln_file.write('>%s\n%s\n' % (k, aln_old[k]))

# run cawlign on all new and updated sequences
def run_cawlign(seqs_new, to_add, to_replace, out_aln_file, cawlign_path=DEFAULT_CAWLIGN_PATH, cawlign_args=DEFAULT_CAWLIGN_ARGS):
    new_fasta_data = ''.join('>%s\n%s\n' % (k,seqs_new[k]) for k in (to_add | to_replace)).encode('utf-8')
    cawlign_command = [cawlign_path] + [v.strip() for v in cawlign_args.split()]
    run(cawlign_command, input=new_fasta_data, stdout=out_aln_file)

# main program
def main():
    print_log("Running cawlign True Append v%s" % CAWLIGN_TRUE_APPEND_VERSION)
    args = parse_args()
    print_log("Command: %s" % ' '.join(argv))
    print_log("Loading user FASTA: %s" % args.fasta_file)
    seqs_new = load_fasta(args.fasta_file)
    print_log("- Num Sequences: %s" % len(seqs_new))
    print_log("Parsing old FASTA: %s" % args.old_unaligned_file)
    seqs_old = load_fasta(args.old_unaligned_file)
    print_log("- Num Sequences: %s" % (len(seqs_old)))
    print_log("Determining deltas between user table and old table...")
    to_add, to_replace, to_delete, to_keep = determine_deltas(seqs_new, seqs_old)
    print_log("- Add: %s" % len(to_add))
    print_log("- Replace: %s" % len(to_replace))
    print_log("- Delete: %s" % len(to_delete))
    print_log("- Do nothing: %s" % (len(to_keep)))
    print_log("Loading unchanged alignments from file: %s" % args.old_aligned_file)
    aln_old = load_fasta(args.old_aligned_file)
    print_log("Creating output alignment file: %s" % args.output_aligned_file)
    with open_file(args.output_aligned_file, 'w') as out_aln_file:
        print_log("Aligning new and updated sequences...")
        run_cawlign(seqs_new, to_add, to_replace, out_aln_file, cawlign_path=args.cawlign_path, cawlign_args=args.cawlign_args)
        print_log("Copying unchanged alignments...")
        copy_unchanged_alignments(to_keep, aln_old, out_aln_file)

# run main program
if __name__ == "__main__":
    main()
