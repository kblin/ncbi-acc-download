# Copyright 2017,2018 Kai Blin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Core functions of the ncbi-by-accession downloader."""
from __future__ import print_function
import functools
from io import StringIO
import sys
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from ncbi_acc_download.download import (
    build_params,
    get_stream,
    get_url_by_format,
    write_stream,
)
from ncbi_acc_download.errors import ValidationError
from ncbi_acc_download.validate import (
    HAVE_BIOPYTHON,
    run_extended_validation,
    VALIDATION_LEVELS,
)
from ncbi_acc_download.wgs import download_wgs_parts

ENTREZ_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
SVIEWER_URL = 'https://eutils.ncbi.nlm.nih.gov/sviewer/viewer.cgi'


class Config(object):
    """NCBI genome download configuration."""

    __slots__ = (
        'emit',
        'entrez_url',
        '_extended_validation',
        'format',
        'keep_filename',
        'molecule',
        'recursive',
        'sviewer_url',
        'verbose',
    )

    # TODO: once python2 support can be dropped, switch to explicit argnames + * to drop extra args
    def __init__(self, **kwargs):
        """Initialise the config from scratch."""
        self.extended_validation = kwargs.get('extended_validation', 'none')
        self.molecule = kwargs.get('molecule', 'nucleotide')
        self.keep_filename = 'out' in kwargs
        self.recursive = kwargs.get('recursive', False)

        self.entrez_url = kwargs.get('entrez_url', ENTREZ_URL)
        self.sviewer_url = kwargs.get('sviewer_url', SVIEWER_URL)

        if self.molecule == 'nucleotide':
            self.format = kwargs.get('format', 'genbank')
        else:
            self.format = 'fasta'
        self.verbose = kwargs.get('verbose', False)

        def noop(arg):
            """Don't do anything."""
            pass

        self.emit = noop
        if self.verbose:
            self.emit = functools.partial(print, file=sys.stderr, end='', flush=True)

    @property
    def extended_validation(self):
        """Get the extended validation setting."""
        return self._extended_validation

    @extended_validation.setter
    def extended_validation(self, value):
        if value != 'none' and not HAVE_BIOPYTHON:
            raise ValueError("Asked for extended validation, but Biopython not available")
        if value not in VALIDATION_LEVELS:
            raise ValueError("Invalid validation level {}".format(value))
        self._extended_validation = value

    @classmethod
    def from_args(cls, args):
        """Initialise from argpase.Namespace object."""
        config = cls(**args.__dict__)
        return config


def download_to_file(dl_id, config, filename=None, append=False):
    """Download a single ID from NCBI and store it to a file."""
    # types: string, Config, string, bool -> None
    mode = 'a' if append else 'w'

    url = get_url_by_format(config)
    params = build_params(dl_id, config)

    r = get_stream(url, params)
    config.emit("Downloading {}\n".format(r.url))
    if config.keep_filename:
        outfile_name = filename
    else:
        outfile_name = _generate_filename(params, filename)

    with open(outfile_name, mode) as fh:
        _validate_and_write(r, fh, dl_id, config)


def generate_url(dl_id, config):
    """Generate the Entrez URL to download a file using a separate tool"""
    # types: string, Config -> string

    url = get_url_by_format(config)
    params = build_params(dl_id, config)

    # remove the tool field, some other tool will do the download
    del params['tool']
    encoded_params = urlencode(params, doseq=True)
    return "?".join([url, encoded_params])


def _generate_filename(params, filename):
    safe_ids = params['id'][:20].replace(' ', '_')
    file_ending = '.fa'

    if params.get('rettype') == 'gbwithparts':
        file_ending = '.gbk'
    elif params.get('rettype') == 'ft':
        file_ending = '.ft'
    elif params.get('report') == 'gff3':
        file_ending = '.gff'

    if filename:
        outfile_name = "{filename}{ending}".format(filename=filename, ending=file_ending)
    else:
        outfile_name = "{ncbi_id}{ending}".format(ncbi_id=safe_ids, ending=file_ending)

    return outfile_name


def _validate_and_write(request, orig_handle, dl_id, config):
    if config.extended_validation != 'none' or config.recursive:
        handle = StringIO()
    else:
        handle = orig_handle

    write_stream(request, handle, dl_id, config)

    if config.recursive:
        downloaded = download_wgs_parts(handle, config)
        handle = downloaded

    if config.extended_validation != 'none':
        if not run_extended_validation(handle, config.format, config.extended_validation):
            raise ValidationError("Sequence(s) downloaded for {} failed to load.".format(dl_id))


    if config.extended_validation != 'none' or config.recursive:
        orig_handle.write(handle.getvalue())
