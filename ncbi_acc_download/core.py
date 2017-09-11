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
"""Core functions of the ncbi-by-accession downloader"""
from __future__ import print_function
import requests
import sys
try:
    from httplib import IncompleteRead
except ImportError:
    from http.client import IncompleteRead


NCBI_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
ERROR_PATTERNS = (
    b'Error reading from remote server',
    b'Bad gateway',
    b'Cannot process ID list',
    b'server is temporarily unable to service your request',
    b'Service unavailable',
    b'Server Error',
    b'ID list is empty',
    b'Resource temporarily unavailable',
)


def download_from_ncbi(dl_id, molecule="nucleotide"):
    # types: string, string -> None
    params = dict(tool='antiSMASH', retmode='text')

    # delete / characters and as NCBI ignores IDs after #, do the same.
    params['id'] = dl_id

    params['db'] = molecule

    if molecule == 'nucleotide':
        params['rettype'] = 'gbwithparts'
        file_ending = ".gbk"
    else:
        params['rettype'] = 'fasta'
        file_ending = ".fa"

    try:
        r = requests.get(NCBI_URL, params=params, stream=True)
    except (requests.exceptions.RequestException, IncompleteRead) as e:
        print("Failed to download {!r} from NCBI".format(dl_id), file=sys.stderr)
        raise

    if r.status_code != requests.codes.ok:
        print("Failed to download file with id {} from NCBI".format(dl_id), file=sys.stderr)
        raise Exception("Download failed")

    safe_ids = params['id'][:20].replace(' ', '_')
    outfile_name = "{ncbi_id}{ending}".format(ncbi_id=safe_ids, ending=file_ending)

    with open(outfile_name, 'wb') as fh:
        # use a chunk size of 4k, as that's what most filesystems use these days
        for chunk in r.iter_content(4096):
            for pattern in ERROR_PATTERNS:
                if pattern in chunk:
                    raise Exception("Failed to download file with id {} from NCBI: {}".format(
                        params['id'], pattern))

            fh.write(chunk)



