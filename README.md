# HIV-TRACE True Append

## TN93

```bash
./tn93_true_append.py -it example/tn93/Network-New-4.csv -iT example/tn93/Network-New-3.csv -iD example/tn93/Network-New-3.tn93.csv | pigz -9 -p 8 > tmp.tn93.csv.gz
```

To feed the input files via named pipes (e.g. to feed from gzipped files, from a non-flat-file dataset, etc.):

```bash
./tn93_true_append.py -it <(cat example/tn93/Network-New-4.csv) -iT <(cat example/tn93/Network-New-3.csv) -iD <(cat example/tn93/Network-New-3.tn93.csv) | pigz -9 -p 8 > tmp.tn93.csv.gz
```

## DataQC

The original DataQC command is the following:

```bash
DataQCv2.py -t $(which tn93) -d true_append_items/DRAM.csv -c true_append_items/new_orig.csv
```

The True Append command is the following:

```bash
./dataqc_true_append.py -py $(which DataQCv2.py) -t $(which tn93) -d true_append_items/DRAM.csv -c true_append_items/new_orig.csv -oc true_append_items/old_orig.csv -of true_append_items/output/old_orig.csv.fasta -f true_append_items/new_orig.fasta -or true_append_items/output/old_orig.full_report.csv
```

## bealign

The original `bealign` command is the following:

```bash
bealign -r true_append_items/HXB2_1497.fasta -m BLOSUM62 -R true_append_items/new.fasta true_append_items/new.bam
```

The True Append command is the following:

```bash
./bealign_true_append.py -of true_append_items/old.fasta -ob true_append_items/old.bam true_append_items/new.fasta true_append_items/new.true_append.bam
```

## cawlign

The original `cawlign` command is the following:

```bash
cawlign -o new.aln example/cawlign/new.fas
```

The True Append command is the following:

```bash
./cawlign_true_append.py -o new.aln -of example/cawlign/old.fas -oa example/cawlign/old.aln example/cawlign/new.fas
```
