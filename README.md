# HIV-TRACE True Append

## TN93

```bash
./tn93_true_append.py -it example/Network-New-4.csv -iT example/Network-New-3.csv -iD example/Network-New-3.tn93.csv | pigz -9 -p 8 > tmp.tn93.csv.gz
```

To feed the input files via named pipes (e.g. to feed from gzipped files, from a non-flat-file dataset, etc.):

```bash
./tn93_true_append.py -it <(cat example/Network-New-4.csv) -iT <(cat example/Network-New-3.csv) -iD <(cat example/Network-New-3.tn93.csv) | pigz -9 -p 8 > tmp.tn93.csv.gz
```

## DataQC

The original DataQC command is the following:

```bash
DataQCv2.py -t $(which tn93) -d real_data/bak/DRAM.csv -c real_data/new_orig.csv
```

The True Append command is the following:

```bash
./dataqc_true_append.py -py $(which DataQCv2.py) -t $(which tn93) -d real_data/bak/DRAM.csv -c real_data/new_orig.csv -oc real_data/old_orig.csv -of real_data/output/old_orig.csv.fasta -f real_data/new_orig.fasta -or real_data/output/old_orig.full_report.csv
```

## `bealign`

The original `bealign` command is the following:

```bash
bealign -r real_data/bak/HXB2_1497.fasta -m BLOSUM62 -R real_data/new.fasta real_data/new.bam
```

The True Append command is the following:

```bash
./bealign_true_append.py --bealign_args '-r real_data/bak/HXB2_1497.fasta -m BLOSUM62 -R' -of real_data/old.fasta -ob real_data/old.bam real_data/new.fasta real_data/new.true_append.bam
```

## `cawlign`

The original `cawlign` command is the following:

```bash
cawlign -o new.aln example/cawlign/new.fas
```

The True Append command is the following:

```bash
./cawlign_true_append.py -o new.aln -of example/cawlign/old.fas -oa example/cawlign/old.aln example/cawlign/new.fas
```

# End-to-End Tests

## From Scratch (no append)

```bash
DataQCv2.py -c real_data/from_scratch/844144ea-17cc-4025-96b2-e3a21ce8e3fd_orig.csv -d real_data/from_scratch/DRAM.csv -f real_data/from_scratch/844144ea-17cc-4025-96b2-e3a21ce8e3fd.fasta -t $(which tn93) > real_data/from_scratch/844144ea-17cc-4025-96b2-e3a21ce8e3fd.dataqc.log
```
