#!/usr/bin/env python
"""Get sequences from NCBI by GenBank/RefSeq ID"""

from argparse import ArgumentParser

from .core import download_from_ncbi

def main():
    parser = ArgumentParser()

    parser.add_argument('ids', nargs='+', metavar='NCBI-accession')
    parser.add_argument('-m', '--molecule', default="nucleotide", choices=["nucleotide", "protein"],
                        help="Molecule type to download. Default: %(default)s")

    opts = parser.parse_args()

    for dl_id in opts.ids:
        download_from_ncbi(dl_id, opts.molecule)


if __name__ == "__main__":
    main()
