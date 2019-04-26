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
"""Recursively download the actual entries for WGS records."""

import sys

# In python2, SeqIO.write insists on writing 'str', so make sure
# the temporary handle accepts that.
# TODO: Remove this once we drop 2.7 support
if sys.version_info[0] >= 3:  # pragma: no cover
    from io import StringIO
else:  # pragma: no cover
    from StringIO import StringIO

from ncbi_acc_download.download import (
    build_params,
    get_stream,
    get_url_by_format,
    write_stream,
)

try:
    from Bio import SeqIO
    from Bio.Seq import UnknownSeq
    HAVE_BIOPYTHON = True
except ImportError:  # pragma: no cover
    HAVE_BIOPYTHON = False

STEP_SIZE = 10


class WgsRange:
    def __init__(self, identifier, width, start, end):
        self.identifier = identifier
        self.width = width
        self.start = start
        self.end = end

    def get_ids(self):
        """Get the list of identifier strings covered by the range."""
        ids = []
        for i in range(self.start, self.end+1):
            ids.append("{s.identifier}{i:0{s.width}}".format(i=i, s=self))

        return ids

    @classmethod
    def from_string(cls, range_string):
        if '-' not in range_string:
            first = last = range_string
        else:
            first, last = range_string.split('-', 1)

        if '-' in last:
            raise ValueError("More than one hyphen in input.")

        if '.' in first:
            first, _ = first.split('.', 1)

        if '.' in last:
            last, _ = last.split('.', 1)

        identifier = ""
        for i, char in enumerate(first):
            if not char.isdigit():
                identifier += char
            else:
                break

        width = len(first) - len(identifier)

        if width < 1:
            raise ValueError("String identifier is too large.")

        if not last.startswith(identifier):
            raise ValueError("Failed to find shared identifier.")

        first_int = int(first[-width:])
        last_int = int(last[-width:])

        if last_int < first_int:
            raise ValueError("Last identifier smaller than first.")

        return cls(identifier, width, first_int, last_int)


def download_wgs_parts(handle, config):
    """Download all parts of all WGS records in a file handle."""

    if not HAVE_BIOPYTHON:
        return handle

    updated_records = []

    handle.seek(0)
    records = list(SeqIO.parse(handle, config.format))
    for record in records:
        run_download = isinstance(record.seq, UnknownSeq)
        if run_download and ('wgs_scafld' in record.annotations or
                             'wgs' in record.annotations):
            updated_records.extend(download_wgs_for_record(record, config))
        elif run_download and 'contig' in record.annotations:
            updated_records.extend(fix_supercontigs(record, config))
        else:
            updated_records.append(record)

    outhandle = StringIO()
    SeqIO.write(updated_records, outhandle, config.format)
    outhandle.seek(0)
    return outhandle


def download_wgs_for_record(record, config):
    """Download all WGS records in a record."""
    if 'wgs_scafld' in record.annotations:
        # Biopython splits on '-' for us, but doesn't actually calculate the range
        # Also this is somehow a list of lists
        wgs_range = WgsRange.from_string('-'.join(record.annotations['wgs_scafld'][0]))
    elif 'wgs' in record.annotations:
        # Biopython splits on '-' for us, but doesn't actually calculate the range
        # Unlike WGS_SCAFLD, this is just a list
        wgs_range = WgsRange.from_string('-'.join(record.annotations['wgs']))
    else:
        return [record]

    handle = StringIO()
    id_list = wgs_range.get_ids()

    i = 0
    while i < len(id_list):
        dl_id = ",".join(id_list[i:i + STEP_SIZE])
        i += STEP_SIZE

        url = get_url_by_format(config)
        params = build_params(dl_id, config)

        r = get_stream(url, params)
        config.emit("Downloading {}\n".format(r.url))

        write_stream(r, handle, dl_id, config)

    # Rewind, so Biopython can parse this
    handle.seek(0)

    return list(SeqIO.parse(handle, config.format))


def fix_supercontigs(record, config):
    """Fix a record containing a CONTIG entry instead of a seq."""

    handle = StringIO()

    # Let the NCBI assemble the proper record for us by asking for the right format.
    dl_id = record.id
    url = get_url_by_format(config)
    params = build_params(dl_id, config)
    r = get_stream(url, params)
    config.emit("Downloading {}\n".format(r.url))

    write_stream(r, handle, dl_id, config)

    # Rewind, so Biopython can parse this
    handle.seek(0)

    return list(SeqIO.parse(handle, config.format))
