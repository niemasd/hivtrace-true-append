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

```bash
DataQCv2.py -t $(which tn93) -d true_append_items/DRAM.csv -c true_append_items/36cecaff-fec9-4d55-bf66-476ffdc5fde9_orig.csv
```
