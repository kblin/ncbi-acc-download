#!/usr/bin/env python
"""Get sequences from NCBI by GenBank/RefSeq ID."""

from argparse import ArgumentParser, SUPPRESS

from .core import download_to_file, generate_url, Config, HAVE_BIOPYTHON


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
                        choices=('fasta', 'genbank'),
                        help="File format to download nucleotide sequences in. Default: %(default)s")
    parser.add_argument('-o', '--out', default=SUPPRESS,
                        help="Base filename to use for output files. By default, use the NCBI ID.")
    parser.add_argument('--url', action="store_true", default=False,
                        help="Instead of downloading the sequences, just print the URLs to stdout.")
    parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help="Print a progress indicator.")

    opts = parser.parse_args()

    config = Config.from_args(opts)

    for i, dl_id in enumerate(opts.ids):
        filename = None
        if 'out' in opts:
            filename = "{fn}_{i}".format(fn=opts.out, i=i)
        if opts.url:
            print(generate_url(dl_id, config))
        else:
            download_to_file(dl_id, config, filename)


if __name__ == "__main__":
    main()

