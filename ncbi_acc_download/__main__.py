#!/usr/bin/env python
"""Get sequences from NCBI by GenBank/RefSeq ID."""

from argparse import ArgumentParser, SUPPRESS
import sys

from .core import download_to_file, generate_url, Config, HAVE_BIOPYTHON
from .errors import (
    DownloadError,
    InvalidIdError,
)


def main():
    """Command line handling."""
    parser = ArgumentParser()

    parser.add_argument('ids', nargs='+', metavar='NCBI-accession')
    parser.add_argument('-m', '--molecule', default="nucleotide", choices=["nucleotide", "protein"],
                        help="Molecule type to download. Default: %(default)s")
    if HAVE_BIOPYTHON:
        parser.add_argument('-e', '--extended-validation', action="store", default='none',
                            choices=('none', 'loads', 'all'),
                            help="Perform extended validation. Possible options are 'none' to skip validation, "
                                 "'loads' to check if the sequence file loads in Biopython, "
                                 "or 'all' to run all checks. Default: %(default)s")
    parser.add_argument('-F', '--format', action="store", default='genbank',
                        choices=('fasta', 'genbank', 'featuretable', 'gff3'),
                        help="File format to download nucleotide sequences in. Default: %(default)s")
    parser.add_argument('-o', '--out', default=SUPPRESS,
                        help="Single filename to use for the combined output.")
    parser.add_argument('-p', '--prefix', default=SUPPRESS,
                        help="Filename prefix to use for output files instead of using the NCBI ID.")
    if HAVE_BIOPYTHON:
        parser.add_argument('-r', '--recursive', action="store_true", default=False,
                            help="Recursively get all entries of a WGS entry.")
    parser.add_argument('--url', action="store_true", default=False,
                        help="Instead of downloading the sequences, just print the URLs to stdout.")
    parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help="Print a progress indicator.")

    opts = parser.parse_args()

    config = Config.from_args(opts)

    # TODO: Change this to download multiple records at once?
    for i, dl_id in enumerate(opts.ids):
        filename = None
        append = False
        if 'prefix' in opts:
            filename = "{fn}_{i}".format(fn=opts.prefix, i=i)
        elif 'out' in opts:
            filename = opts.out
            append = (i > 0)

        try:
            if opts.url:
                print(generate_url(dl_id, config))
            else:
                download_to_file(dl_id, config, filename, append)
        except InvalidIdError as err:
            print("NCBI Entrez returned error code {e.status_code}, are ID(s) {e.ids} valid?".format(e=err))
            sys.exit(1)
        except DownloadError as err:
            print(err, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

