from io import StringIO
import pytest
import requests
import os
from ncbi_acc_download.core import Config
from ncbi_acc_download.errors import DownloadError
from ncbi_acc_download import download
from ncbi_acc_download import validate

def full_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), name))

def test_download_and_validate_partial_wgs(req):
    handle = StringIO(open(full_path('partialcontig.gbk'), 'r').read())
    assert validate.run_extended_validation(handle, 'genbank', 'loads')

    try:
        from Bio import SeqIO
        handle.seek(0)
        records = list(SeqIO.parse(handle, 'genbank'))
        assert len(records)==1
        assert len(records[0].features)==5
    except ModuleNotFoundError:
        pass

    ## overwrites data in stringIO handle
    assert validate.run_extended_validation(handle, 'genbank', 'correct')
    try:
        from Bio import SeqIO
        handle.seek(0)
        records = list(SeqIO.parse(handle, 'genbank'))
        assert len(records)==1
        assert len(records[0].features)==1
    except ModuleNotFoundError:
        pass
