#! /usr/bin/env python3
'''
Compare 2 FASTA files
'''
from gzip import open as gopen
from sys import argv

# load FASTA
def load_fasta(fn):
    if fn.strip().lower().endswith('.gz'):
        infile = gopen(fn, 'rt')
    else:
        infile = open(fn, 'r')
    seqs = dict(); name = None; seq = ''
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
    seqs[name] = seq
    return seqs

# compare 2 FASTAs
def compare_fasta(fn1, fn2):
    seqs1 = load_fasta(fn1); seqs2 = load_fasta(fn2)
    seqs_equal = list(); seqs_unequal = list(); seqs_fn1_not_fn2 = list(); seqs_fn2_not_fn1 = list()
    for k in seqs1:
        if k in seqs2:
            if seqs1[k].upper() == seqs2[k].upper():
                seqs_equal.append(k)
            else:
                seqs_unequal.append(k)
        else:
                seqs_fn1_not_fn2.append(k)
    for k in seqs2:
        if k not in seqs1:
            seqs_fn2_not_fn1.append(k)
    print("Same Sequence: %d" % len(seqs_equal))
    print("Diff Sequence: %d" % len(seqs_unequal))
    print("Missing in '%s': %d" % (fn1, len(seqs_fn2_not_fn1)))
    print("Missing in '%s': %d" % (fn2, len(seqs_fn1_not_fn2)))

# run tool
if __name__ == "__main__":
    if len(argv) != 3:
        print("USAGE: %s <fasta_1> <fasta_2>" % argv[0]); exit(1)
    compare_fasta(argv[1], argv[2])
