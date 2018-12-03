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


class BadPatternError(DownloadError):
    """Error thrown when download file contains an error pattern."""

    pass


class ValidationError(DownloadError):
    """Error thrown when download file failes extended validation."""

    pass
