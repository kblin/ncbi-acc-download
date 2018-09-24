# Copyright 2017 Kai Blin
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
import requests
import sys
try:
    from httplib import IncompleteRead
except ImportError:
    from http.client import IncompleteRead
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
from ncbi_acc_download.validate import HAVE_BIOPYTHON, run_extended_validation, VALIDATION_LEVELS


NCBI_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
ERROR_PATTERNS = (
    u'Error reading from remote server',
    u'Bad gateway',
    u'Bad Gateway',
    u'Cannot process ID list',
    u'server is temporarily unable to service your request',
    u'Service unavailable',
    u'Server Error',
    u'ID list is empty',
    u'Resource temporarily unavailable',
    u'Failed to retrieve sequence',
    u'Failed to understand id',
)


class DownloadError(RuntimeError):
    """Base error for all problems when downloading from NCBI."""

    pass


class BadPatternError(DownloadError):
    """Error thrown when download file contains an error pattern."""

    pass


class ValidationError(DownloadError):
    """Error thrown when download file failes extended validation."""

    pass


class Config(object):
    """NCBI genome download configuration."""

    __slots__ = (
        'emit',
        '_extended_validation',
        'format',
        'molecule',
        'verbose',
    )

    # TODO: once python2 support can be dropped, switch to explicit argnames + * to drop extra args
    def __init__(self, **kwargs):
        """Initialise the config from scratch."""
        self.extended_validation = kwargs.get('extended_validation', 'none')
        self.molecule = kwargs.get('molecule', 'nucleotide')
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


def download_to_file(dl_id, config, filename=None):
    """Download a single ID from NCBI and store it to a file."""
    # types: string, Config, string -> None

    params = build_params(dl_id, config)

    r = get_stream(params)
    config.emit("Downloading {}\n".format(r.url))
    outfile_name = _generate_filename(params, filename)

    with open(outfile_name, 'w') as fh:
        _validate_and_write(r, fh, dl_id, config)


def generate_url(dl_id, config):
    """Generate the Entrez URL to download a file using a separate tool"""
    # types: string, Config -> string

    params = build_params(dl_id, config)

    # remove the tool field, some other tool will do the download
    del params['tool']
    encoded_params = urlencode(params, doseq=True)
    return "?".join([NCBI_URL, encoded_params])


def get_stream(params):
    """Get the actual streamed request from NCBI."""
    try:
        r = requests.get(NCBI_URL, params=params, stream=True)
    except (requests.exceptions.RequestException, IncompleteRead) as e:
        print("Failed to download {!r} from NCBI".format(params['id']), file=sys.stderr)
        raise DownloadError(str(e))

    if r.status_code != requests.codes.ok:
        print("Failed to download file with id {} from NCBI".format(params['id']), file=sys.stderr)
        raise DownloadError("Download failed with return code: {}".format(r.status_code))

    return r


def build_params(dl_id, config):
    """Build the query parameters for the Entrez query."""
    params = dict(tool='ncbi-acc-download', retmode='text')

    # delete / characters and as NCBI ignores IDs after #, do the same.
    params['id'] = dl_id

    params['db'] = config.molecule

    if config.molecule == 'nucleotide' and config.format == 'genbank':
        params['rettype'] = 'gbwithparts'
    else:
        params['rettype'] = 'fasta'

    return params


def _generate_filename(params, filename):
    safe_ids = params['id'][:20].replace(' ', '_')
    file_ending = '.fa'

    if params['rettype'] == 'gbwithparts':
        file_ending = '.gbk'

    if filename:
        outfile_name = "{filename}{ending}".format(filename=filename, ending=file_ending)
    else:
        outfile_name = "{ncbi_id}{ending}".format(ncbi_id=safe_ids, ending=file_ending)

    return outfile_name


def _validate_and_write(request, orig_handle, dl_id, config):
    if config.extended_validation != 'none':
        handle = StringIO()
    else:
        handle = orig_handle

    # use a chunk size of 4k, as that's what most filesystems use these days
    for chunk in request.iter_content(4096, decode_unicode=True):
        config.emit(u'.')
        for pattern in ERROR_PATTERNS:
            if pattern in chunk:
                raise BadPatternError("Failed to download file with id {} from NCBI: {}".format(
                    dl_id, pattern))

        handle.write(chunk)
    config.emit(u'\n')

    if config.extended_validation == 'none':
        return

    if not run_extended_validation(handle, config.format, config.extended_validation):
        raise ValidationError("Sequence(s) downloaded for {} failed to load.".format(dl_id))
    orig_handle.write(handle.getvalue())
