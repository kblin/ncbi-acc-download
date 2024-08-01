"""Test the WGS download helper functions."""

from io import StringIO
import os
import pytest

from ncbi_acc_download.core import Config
from ncbi_acc_download.core import ENTREZ_URL
from ncbi_acc_download import wgs
from ncbi_acc_download.wgs import WgsRange


def full_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), name))


def test_init():
    wgs_range = WgsRange("ABCD", 5, 1, 3)
    assert wgs_range.identifier == "ABCD"
    assert wgs_range.width == 5
    assert wgs_range.start == 1
    assert wgs_range.end == 3

    wgs_range = WgsRange("ABCD", 5, 1, 1)
    assert wgs_range.identifier == "ABCD"
    assert wgs_range.width == 5
    assert wgs_range.start == 1
    assert wgs_range.end == 1


def test_get_ids():
    wgs_range = WgsRange("ABCD", 5, 1, 3)

    expected = ["ABCD00001", "ABCD00002", "ABCD00003"]
    assert wgs_range.get_ids() == expected

    wgs_range = WgsRange("ABCD", 5, 1, 1)
    expected = ["ABCD00001"]
    assert wgs_range.get_ids() == expected


def test_from_string():
    range_string = "ABCD01000001.1-ABCD01000022.1"
    wgs_range = WgsRange.from_string(range_string)
    assert wgs_range.identifier == "ABCD"
    assert wgs_range.width == 8
    assert wgs_range.start == 1000001
    assert wgs_range.end == 1000022

    # Some records like JOAR00000000.1 only have a single entry in WGS_SCAFLD
    wgs_range = WgsRange.from_string("ABCD123")
    assert wgs_range.identifier == "ABCD"
    assert wgs_range.width == 3
    assert wgs_range.start == 123
    assert wgs_range.end == 123
    assert wgs_range.get_ids() == ["ABCD123"]

    with pytest.raises(ValueError, match="More than one hyphen in input."):
        _ = WgsRange.from_string("ABCD123-ABCD234-ABCD345")

    with pytest.raises(ValueError, match="String identifier is too large."):
        _ = WgsRange.from_string("ABCD-ABCD")

    with pytest.raises(ValueError, match="Failed to find shared identifier."):
        _ = WgsRange.from_string("ABCD123-EFGH234")

    with pytest.raises(ValueError, match="Last identifier smaller than first."):
        _ = WgsRange.from_string("ABCD234-ABCD123")


def test_download_wgs_parts_no_biopython():
    old_have_biopython = wgs.HAVE_BIOPYTHON
    wgs.HAVE_BIOPYTHON = False

    cfg = Config(format="genbank")

    handle = StringIO()

    new_handle = wgs.download_wgs_parts(handle, cfg)
    wgs.HAVE_BIOPYTHON = old_have_biopython
    assert handle == new_handle


def _build_request_params(filename):
    return {
        "headers": {"Content-Type": "text/plain; charset=UTF-8"},
        "body": open(full_path(filename), "rb"),
    }


def test_download_wgs_parts_wgs(req):
    cfg = Config(format="genbank")
    wgs_contig = open(full_path('wgs.gbk'), 'rt')
    req.get(ENTREZ_URL, **_build_request_params('wgs_full.gbk'))

    outhandle = wgs.download_wgs_parts(wgs_contig, cfg)
    wgs_full = open(full_path('wgs_full.gbk'), 'rt')
    assert outhandle.getvalue() == wgs_full.read()
    wgs_full.close()
    wgs_contig.close()


def test_download_wgs_parts_wgs_retry(req):
    cfg = Config(format="genbank")
    wgs_contig = open(full_path('wgs.gbk'), 'rt')
    req.get(ENTREZ_URL, response_list=[
        {"text": u'Whoa, slow down', "status_code": 429, "headers": {"Retry-After": "0"}},
        _build_request_params('wgs_full.gbk'),
    ])

    outhandle = wgs.download_wgs_parts(wgs_contig, cfg)
    wgs_full = open(full_path('wgs_full.gbk'), 'rt')
    assert outhandle.getvalue() == wgs_full.read()
    wgs_full.close()
    wgs_contig.close()


def test_download_wgs_parts_wgs_scafld(req):
    cfg = Config(format="genbank")
    wgs_contig = open(full_path('wgs_scafld.gbk'), 'rt')
    with open(full_path('wgs_full.gbk'), 'rt') as handle:
        full_file = handle.read()
    req.get(ENTREZ_URL, text=full_file)

    outhandle = wgs.download_wgs_parts(wgs_contig, cfg)
    assert outhandle.getvalue() == full_file
    wgs_contig.close()


def test_download_wgs_parts_supercontig(req):
    cfg = Config(format="genbank")
    supercontig = open(full_path('supercontig.gbk'), 'rt')
    req.get(ENTREZ_URL, **_build_request_params('supercontig_full.gbk'))

    outhandle = wgs.download_wgs_parts(supercontig, cfg)
    supercontig_full = open(full_path('supercontig_full.gbk'), 'rt')
    assert outhandle.getvalue() == supercontig_full.read()
    supercontig_full.close()
    supercontig.close()


def test_download_wgs_parts_supercontig_retry(req):
    cfg = Config(format="genbank")
    supercontig = open(full_path('supercontig.gbk'), 'rt')
    req.get(ENTREZ_URL, response_list=[
        {"text": u'Whoa, slow down', "status_code": 429, "headers": {"Retry-After": "0"}},
        _build_request_params('supercontig_full.gbk'),
    ])

    outhandle = wgs.download_wgs_parts(supercontig, cfg)
    supercontig_full = open(full_path('supercontig_full.gbk'), 'rt')
    assert outhandle.getvalue() == supercontig_full.read()
    supercontig_full.close()
    supercontig.close()


def test_download_wgs_no_parts(req):
    cfg = Config(format="genbank")
    supercontig = open(full_path('supercontig_full.gbk'), 'rt')
    req.get(ENTREZ_URL, status_code=404)

    outhandle = wgs.download_wgs_parts(supercontig, cfg)
    supercontig_full = open(full_path('supercontig_full.gbk'), 'rt')
    assert outhandle.getvalue() == supercontig_full.read()
    supercontig_full.close()
    supercontig.close()


@pytest.mark.xfail
def test_download_wgs_parts_tsa(req):
    cfg = Config(format="genbank")
    wgs_contig = open(full_path('tsa.gbk'), 'rt')
    req.get(ENTREZ_URL, body=open(full_path('tsa_full.gbk'), 'rt'))

    outhandle = wgs.download_wgs_parts(wgs_contig, cfg)
    wgs_full = open(full_path('tsa_full.gbk'), 'rt')
    assert outhandle.getvalue() == wgs_full.read()
    wgs_full.close()
    wgs_contig.close()
