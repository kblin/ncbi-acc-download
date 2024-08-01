# NCBI accession download script

A partner script to the popular [ncbi-genome-download](https://github.com/kblin/ncbi-genome-download)
script, `ncbi-acc-download` allows you to download sequences from GenBank/RefSeq by accession through
the NCBI [ENTREZ API](https://www.ncbi.nlm.nih.gov/books/NBK184582/).

## Installation

```
pip install ncbi-acc-download
```

Alternatively, clone this repository from GitHub, then run (in a python virtual environment)
```
pip install .
```
If this fails on older versions of Python, try updating your `pip` tool first:
```
pip install --upgrade pip
```
and then rerun the `ncbi-acc-download` install.

`ncbi-acc-download` is only developed and tested on Python releases still under active
support by the Python project. At the moment, this means versions 3.8, 3.9, 3.10, 3.11 and 3.12.
Specifically, no attempt at testing under Python versions older than 3.8 is being made.

`ncbi-acc-download` 0.2.6 was the last version to support Python 2.7.

If your system is stuck on an older version of Python, consider using a tool like
[Homebrew](http://brew.sh) or [Linuxbrew](http://linuxbrew.sh) to obtain a more up-to-date
version.


## Usage

To download a nucleotide record AB_12345 in GenBank format, run
```
ncbi-acc-download AB_12345
```

To download a nucleotide record AB_12345 in FASTA format, run
```
ncbi-acc-download --format fasta AB_12345
```

To download a protein record WP_12345 in FASTA format, run
```
ncbi-acc-download --molecule protein WP_12345
```

To just generate a list of download URLs to run the actual download elsewhere, run
```
ncbi-acc-download --url AB_12345
```

If you want to concatenate multiple sequences into a single file, run
```
ncbi-acc-download --out two_genomes.gbk AB_12345 AB_23456
```

You can use this with `/dev/stdout` as the filename to print the downloaded data to
standard output instead of writing to a file if you want to chain `ncbi-acc-download` with other
command line tools, like so:
```
ncbi-genome-download --out /dev/stdout --format fasta AB_12345 AB_23456 | gzip > two_genomes.fa.gz
```

If you want to download all records covered by a WGS master record instead of the master record itself,
run
```
ncbi-acc-download --recursive NZ_EXMP01000000
```

You can supply a genomic range to the accession download using `--range`
```
ncbi-acc-download NC_007194 --range 1001:9000
```
As cutting a record up with a range operator like that can leave partial features at both ends of the
record, you can combine the range download with the new `correct` extended validator to remove the
partial features.
```
ncbi-acc-download NC_007194 --range 1001:9000 --extended-validation correct
```

You can get more detailed information on the download progress by using the `--verbose` or `-v` flag.

To get an overview of all options, run
```
ncbi-acc-download --help
```

## License
All code is available under the Apache License version 2, see the
[`LICENSE`](LICENSE) file for details.
