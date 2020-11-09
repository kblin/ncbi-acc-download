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
"""Custom error classes of the ncbi-by-accession downloader."""


class DownloadError(RuntimeError):
    """Base error for all problems when downloading from NCBI."""

    pass


class InvalidIdError(RuntimeError):
    """Error thrown when Entrez responds with a 4xx error (other than 429)."""

    def __init__(self, message, ids, status_code):
        super().__init__(message)
        self.ids = ids
        self.status_code = status_code


class TooManyRequests(DownloadError):
    """Error thrown when Entrez responds with a 429 error."""

    def __init__(self, message, retry_after):
        super().__init__(message)
        self.retry_after = retry_after


class BadPatternError(DownloadError):
    """Error thrown when download file contains an error pattern."""

    pass


class ValidationError(DownloadError):
    """Error thrown when download file failes extended validation."""

    pass
