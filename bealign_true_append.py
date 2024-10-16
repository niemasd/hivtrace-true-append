#! /usr/bin/env python3
'''
True Append for bealign
'''

# imports
from datetime import datetime
from os.path import isfile
from pysam import AlignmentFile
from subprocess import run
from sys import argv, stderr, stdin, stdout
import argparse

# constants
BEALIGN_TRUE_APPEND_VERSION = '0.0.1'
DEFAULT_BEALIGN_PATH = 'bealign'
DEFAULT_BEALIGN_ARGS = ''
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
    parser.add_argument('-of', '--old_fasta_file', required=True, type=str, help="Input: Old sequences (FASTA)")
    parser.add_argument('-ob', '--old_bam_file', required=True, type=str, help="Input: Old aligned sequences (BAM)")
    parser.add_argument('--bealign_args', required=False, type=str, default=DEFAULT_BEALIGN_ARGS, help="Optional bealign arguments")
    parser.add_argument('--bealign_path', required=False, type=str, default=DEFAULT_BEALIGN_PATH, help="Path to the bealign executable")
    parser.add_argument('fasta_file', type=str, help="Input: User sequences (FASTA)")
    parser.add_argument('bam_file', type=str, help="Output: Aligned sequences (BAM)")
    args = parser.parse_args()
    for fn in [args.fasta_file, args.old_fasta_file, args.old_bam_file]:
        if not isfile(fn) and not fn.startswith('/dev/fd'):
            raise ValueError("File not found: %s" % fn)
    for fn in [args.bam_file]:
        if fn.lower().endswith('.gz'):
            raise ValueError("Cannot directly write to gzip output file")
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

# run bealign on all new and updated sequences
def run_bealign(seqs_new, new_updated_fasta_fn, to_add, to_replace, out_bam_fn, bealign_path=DEFAULT_BEALIGN_PATH, bealign_args=DEFAULT_BEALIGN_ARGS):
    new_updated_fasta_file = open_file(new_updated_fasta_fn, 'w')
    for k, v in seqs_new.items():
        if (k in to_add) or (k in to_replace):
            new_updated_fasta_file.write('>%s\n%s\n' % (k, v))
    bealign_command = [bealign_path] + [v.strip() for v in bealign_args.split()] + [new_updated_fasta_fn, out_bam_fn]
    log_f = open_file('%s.bealign.log' % new_updated_fasta_fn, 'w')
    print_log("Running bealign: %s" % ' '.join(bealign_command))
    run(bealign_command, stderr=log_f); log_f.close()

# merge old and new/updated BAMs
def merge_bams(old_bam_fn, new_updated_bam_fn, out_bam_fn, to_keep):
    old_bam_file = AlignmentFile(old_bam_fn, 'rb')
    new_updated_bam_file = AlignmentFile(new_updated_bam_fn, 'rb')
    out_bam_file = AlignmentFile(out_bam_fn, 'wb', template=new_updated_bam_file)
    for read in new_updated_bam_file.fetch(until_eof=True):
        out_bam_file.write(read)
    for read in old_bam_file.fetch(until_eof=True):
        if read.query_name.strip() in to_keep:
            out_bam_file.write(read)

# main program
def main():
    print_log("Running bealign True Append v%s" % BEALIGN_TRUE_APPEND_VERSION)
    args = parse_args()
    print_log("Command: %s" % ' '.join(argv))
    print_log("Loading user FASTA: %s" % args.fasta_file)
    seqs_new = load_fasta(args.fasta_file)
    print_log("- Num Sequences: %s" % len(seqs_new))
    print_log("Parsing old FASTA: %s" % args.old_fasta_file)
    seqs_old = load_fasta(args.old_fasta_file)
    print_log("- Num Sequences: %s" % (len(seqs_old)))
    print_log("Determining deltas between user table and old table...")
    to_add, to_replace, to_delete, to_keep = determine_deltas(seqs_new, seqs_old)
    print_log("- Add: %s" % len(to_add))
    print_log("- Replace: %s" % len(to_replace))
    print_log("- Delete: %s" % len(to_delete))
    print_log("- Do nothing: %s" % (len(to_keep)))
    new_updated_fasta_fn = '%s.new_updated.fasta' % '.'.join(args.fasta_file.split('.')[:-1])
    new_updated_bam_fn = '%s.new_updated.bam' % '.'.join(args.fasta_file.split('.')[:-1])
    print_log("Aligning new and updated sequences and writing output to: %s" % new_updated_bam_fn)
    run_bealign(seqs_new, new_updated_fasta_fn, to_add, to_replace, new_updated_bam_fn, bealign_path=args.bealign_path, bealign_args=args.bealign_args)
    print_log("Merging old and new/updated alignments into: %s" % args.bam_file)
    merge_bams(args.old_bam_file, new_updated_bam_fn, args.bam_file, to_keep)

# run main program
if __name__ == "__main__":
    main()
