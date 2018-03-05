#!/usr/bin/env python
"""Get sequences from NCBI by GenBank/RefSeq ID."""

from argparse import ArgumentParser, SUPPRESS

from .core import download_from_ncbi, Config


def main():
    """Command line handling."""
    parser = ArgumentParser()

    parser.add_argument('ids', nargs='+', metavar='NCBI-accession')
    parser.add_argument('-m', '--molecule', default="nucleotide", choices=["nucleotide", "protein"],
                        help="Molecule type to download. Default: %(default)s")
    parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help="Print a progress indicator.")

    opts = parser.parse_args()

    config = Config.from_args(opts)

    for dl_id in opts.ids:
        download_from_ncbi(dl_id, config)


if __name__ == "__main__":
    main()

