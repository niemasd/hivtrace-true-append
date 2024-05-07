#! /usr/bin/env python3
'''
Compare 2 TN93 CSV files
'''
from csv import reader
from gzip import open as gopen
from sys import argv

# load TN93 CSV
def load_tn93(fn):
    if fn.strip().lower().endswith('.gz'):
        infile = gopen(fn, 'rt')
    else:
        infile = open(fn, 'r')
    dists = dict()
    for row in reader(infile):
        u, v, d = [x.strip() for x in row]
        try:
            d = float(d)
        except:
            continue # header row
        u, v = sorted([u,v])
        if u not in dists:
            dists[u] = dict()
        if v in dists[u]:
            raise ValueError("Duplicate pairwise distance between '%s' and '%s': %s" % (u, v, fn))
        dists[u][v] = d
    infile.close()
    return dists

# compare 2 TN93 CSVs
def compare_tn93(fn1, fn2):
    dists1 = load_tn93(fn1); dists2 = load_tn93(fn2)
    pairs_equal = list(); pairs_unequal = list(); pairs_fn1_not_fn2 = list(); pairs_fn2_not_fn1 = list()
    for u in dists1:
        for v in dists1[u]:
            if u in dists2 and v in dists2[u]:
                if dists1[u][v] == dists2[u][v]:
                    pairs_equal.append((u,v))
                else:
                    pairs_unequal.append((u,v))
            else:
                pairs_fn1_not_fn2.append((u,v))
    for u in dists2:
        for v in dists2[u]:
            if u not in dists1 or v not in dists1[u]:
                pairs_fn2_not_fn1.append((u,v))
    print("Same Distance: %d pairs" % len(pairs_equal))
    print("Diff Distance: %d pairs" % len(pairs_unequal))
    print("Missing in '%s': %d pairs" % (fn1, len(pairs_fn2_not_fn1)))
    print("Missing in '%s': %d pairs" % (fn2, len(pairs_fn1_not_fn2)))

# run tool
if __name__ == "__main__":
    if len(argv) != 3:
        print("USAGE: %s <tn93_csv_1> <tn93_csv_2>" % argv[0]); exit(1)
    compare_tn93(argv[1], argv[2])
