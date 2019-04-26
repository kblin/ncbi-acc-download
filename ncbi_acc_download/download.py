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
"""The actual download functionality."""

from __future__ import print_function

from collections import OrderedDict
try:
    from httplib import IncompleteRead
except ImportError:
    from http.client import IncompleteRead
import requests
import sys

from ncbi_acc_download.errors import (
    BadPatternError,
    DownloadError,
)

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


def get_url_by_format(config):
    """Get URL depending on the format."""
    # types: Config -> string

    if config.format == 'gff3':
        return config.sviewer_url

    return config.entrez_url


def build_params(dl_id, config):
    """Build the query parameters for the Entrez query."""
    params = OrderedDict(tool='ncbi-acc-download', retmode='text')

    # delete / characters and as NCBI ignores IDs after #, do the same.
    params['id'] = dl_id

    params['db'] = config.molecule

    if config.molecule == 'nucleotide':
        if config.format == 'genbank':
            params['rettype'] = 'gbwithparts'
        elif config.format == 'featuretable':
            params['rettype'] = 'ft'
        elif config.format == 'gff3':
            params['report'] = 'gff3'
        else:
            params['rettype'] = 'fasta'
    else:
        params['rettype'] = 'fasta'

    return params


def get_stream(url, params):
    """Get the actual streamed request from NCBI."""
    try:
        r = requests.get(url, params=params, stream=True)
    except (requests.exceptions.RequestException, IncompleteRead) as e:
        print("Failed to download {!r} from NCBI".format(params['id']), file=sys.stderr)
        raise DownloadError(str(e))

    if r.status_code != requests.codes.ok:
        print("Failed to download file with id {} from NCBI".format(params['id']), file=sys.stderr)
        raise DownloadError("Download failed with return code: {}".format(r.status_code))

    return r


def write_stream(request, handle, dl_id, config):
    """Write all chunks of the request to the handle."""
    # use a chunk size of 4k, as that's what most filesystems use these days
    try:
        for chunk in request.iter_content(4096, decode_unicode=True):
            config.emit(u'.')
            for pattern in ERROR_PATTERNS:
                if pattern in chunk:
                    raise BadPatternError("Failed to download record(s) with id(s) {} from NCBI: {}".format(
                        dl_id, pattern))

            handle.write(chunk)
    except requests.exceptions.ChunkedEncodingError as err:
        print("Download of {!r} aborted: {}".format(dl_id, str(err)), file=sys.stderr)
        raise DownloadError(str(err))
    config.emit(u'\n')

