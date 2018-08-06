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
support by the Python project. At the moment, this means versions 2.7, 3.4, 3.5, 3.6 and 3.7.
Specifically, no attempt at testing under Python versions older than 2.7 or 3.4 is being made.

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

To get an overview of all options, run
```
ncbi-acc-download --help
```

## License
All code is available under the Apache License version 2, see the
[`LICENSE`](LICENSE) file for details.
