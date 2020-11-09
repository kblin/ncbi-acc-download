"""Tests for the core module."""

from argparse import Namespace
from io import StringIO
import pytest
import requests

from ncbi_acc_download import core
from ncbi_acc_download.core import (
    ENTREZ_URL,
    SVIEWER_URL,
)
from ncbi_acc_download.errors import (
    BadPatternError,
    DownloadError,
    InvalidIdError,
    TooManyRequests,
)


def test_config():
    """Test the config class."""
    args = Namespace(molecule="nucleotide", verbose=False)
    config = core.Config.from_args(args)
    assert config.verbose is False
    assert config.molecule == 'nucleotide'
    assert config.extended_validation == 'none'

    args = Namespace(molecule="protein", verbose=True)
    config = core.Config.from_args(args)
    assert config.verbose is True
    assert config.molecule == 'protein'


def test_config_no_biopython(monkeypatch):
    """Test the correct errors are raised if Biopython is not available."""
    monkeypatch.setattr(core, 'HAVE_BIOPYTHON', False)
    assert core.HAVE_BIOPYTHON is False
    args = Namespace(extended_validation='all')
    with pytest.raises(ValueError):
        core.Config.from_args(args)


def test_config_have_biopython():
    """Test we detect Biopython."""
    assert core.HAVE_BIOPYTHON
    args = Namespace(extended_validation='all')
    config = core.Config.from_args(args)
    assert config.extended_validation == 'all'


def test_download_to_file(req, tmpdir):
    """Test downloading things from NCBI."""
    req.get(ENTREZ_URL, text='This works.')
    outdir = tmpdir.mkdir('outdir')
    filename = outdir.join('foo')
    expected = outdir.join('foo.gbk')
    config = core.Config(molecule='nucleotide', verbose=False)

    core.download_to_file('FOO', config, filename=filename)

    assert expected.check()


def test_download_to_file_append(req, tmpdir):
    """Test appending multiple downloads into a single file."""
    req.get(ENTREZ_URL, text='This works.\n')
    outdir = tmpdir.mkdir('outdir')
    filename = outdir.join('foo.txt')
    expected = outdir.join('foo.txt')
    config = core.Config(molecule='nucleotide', verbose=False, out='foo.txt')

    core.download_to_file('FOO', config, filename=str(filename), append=False)
    core.download_to_file('BAR', config, filename=str(filename), append=True)
    core.download_to_file('BAZ', config, filename=str(filename), append=True)

    assert expected.check()
    assert len(expected.readlines()) == 3


def test_download_to_file_retry(req, tmpdir):
    """Test downloading things from NCBI, retrying after a 429 status."""
    req.get(ENTREZ_URL, response_list=[
        {"text": u'Whoa, slow down', "status_code": 429, "headers": {"Retry-After": "0"}},
        {"text": 'This works.'},
    ])
    outdir = tmpdir.mkdir('outdir')
    filename = outdir.join('foo')
    expected = outdir.join('foo.gbk')
    config = core.Config(molecule='nucleotide', verbose=False)

    core.download_to_file('FOO', config, filename=filename)

    assert expected.check()


def test_build_params():
    """Test we build the right set of parameters."""
    config = core.Config(molecule='nucleotide', verbose=False)
    dl_id = 'TEST'
    expected_params = {
        'tool': 'ncbi-acc-download',
        'retmode': 'text',
        'rettype': 'gbwithparts',
        'id': 'TEST',
        'db': 'nucleotide'
    }

    params = core.build_params(dl_id, config)

    assert params == expected_params

    expected_params = {
        'tool': 'ncbi-acc-download',
        'retmode': 'text',
        'rettype': 'fasta',
        'id': 'TEST',
        'db': 'nucleotide'
    }

    config.format = 'fasta'
    params = core.build_params(dl_id, config)

    assert params == expected_params

    expected_params = {
        'tool': 'ncbi-acc-download',
        'retmode': 'text',
        'rettype': 'ft',
        'id': 'TEST',
        'db': 'nucleotide'
    }

    config.format = 'featuretable'
    params = core.build_params(dl_id, config)

    assert params == expected_params

    expected_params = {
        'tool': 'ncbi-acc-download',
        'retmode': 'text',
        'report': 'gff3',
        'id': 'TEST',
        'db': 'nucleotide'
    }

    config.format = 'gff3'
    params = core.build_params(dl_id, config)

    assert params == expected_params

    config = core.Config(molecule='protein', verbose=False)
    expected_params = {
        'tool': 'ncbi-acc-download',
        'retmode': 'text',
        'rettype': 'fasta',
        'id': 'TEST',
        'db': 'protein'
    }

    params = core.build_params(dl_id, config)

    assert params == expected_params


def test_generate_filename():
    """Test output file name generation."""
    params = dict(id='TEST', db='nucleotide', rettype='gbwithparts')

    filename = core._generate_filename(params, 'foo')
    assert filename == 'foo.gbk'

    params['rettype'] = 'fasta'
    filename = core._generate_filename(params, 'foo')
    assert filename == 'foo.fa'

    params['rettype'] = 'ft'
    filename = core._generate_filename(params, 'foo')
    assert filename == 'foo.ft'

    del params['rettype']
    params['report'] = 'gff3'
    filename = core._generate_filename(params, 'foo')
    assert filename == 'foo.gff'

    params = dict(id='TEST', db='protein', rettype='fasta')
    filename = core._generate_filename(params, None)
    assert filename == 'TEST.fa'


def test_validate_and_write_error_pattern_raises(req):
    """Test scanning the download file for error patterns."""
    handle = StringIO()
    req.get('http://fake/', text=u'ID list is empty')
    r = requests.get('http://fake/')
    config = core.Config()

    with pytest.raises(BadPatternError):
        core._validate_and_write(r, handle, 'FAKE', config)

    req.get('http://fake/', text=u'Error: CEFetchPApplication::proxy_stream(): Failed to retrieve sequence: NC_405534')
    r = requests.get('http://fake/')
    with pytest.raises(BadPatternError):
        core._validate_and_write(r, handle, 'FAKE', config)


def test_validate_and_write_emit(req):
    """Test writing prints dots in verbose mode."""
    handle = StringIO()
    req.get('http://fake/', text=u'This is a sequence file, honest.')
    r = requests.get('http://fake/')
    output = StringIO()
    config = core.Config()
    config.emit = output.write
    core._validate_and_write(r, handle, 'FAKE', config)

    assert output.getvalue() == u'.\n'
    assert handle.getvalue() == u'This is a sequence file, honest.'


def test_validate_and_write_extended_validation(req):
    """Test extended validation before writing."""
    handle = StringIO()
    req.get('http://fake/', text=u'>foo\nMAGIC')
    r = requests.get('http://fake/')
    config = core.Config(extended_validation='loads', molecule='protein')
    core._validate_and_write(r, handle, 'FAKE', config)

    assert handle.getvalue() == u'>foo\nMAGIC'


def test_get_stream_exception(req):
    """Test getting a download stream handles exceptions."""
    req.get(ENTREZ_URL, exc=requests.exceptions.RequestException)
    params = dict(id='FAKE')
    with pytest.raises(DownloadError):
        core.get_stream(ENTREZ_URL, params)


def test_get_stream_bad_status(req):
    """Test getting a download stream handles bad status codes."""
    req.get(ENTREZ_URL, text=u'Nope!', status_code=404)
    params = dict(id='FAKE')
    with pytest.raises(InvalidIdError):
        core.get_stream(ENTREZ_URL, params)


def test_get_stream_too_many_requests(req):
    """Test getting a download stream handles bad status codes."""
    req.get(ENTREZ_URL, text=u'Whoa, slow down', status_code=429, headers={"Retry-After": "2"})
    params = dict(id='FAKE')
    with pytest.raises(TooManyRequests):
        core.get_stream(ENTREZ_URL, params)


def test_generate_url():
    """Test URL generation."""
    config = core.Config()
    expected = "{}?{}".format(ENTREZ_URL, "retmode=text&id=FAKE&db=nucleotide&rettype=gbwithparts")
    assert expected == core.generate_url("FAKE", config)

    config.format = 'gff3'
    expected = "{}?{}".format(SVIEWER_URL, "retmode=text&id=FAKE&db=nucleotide&report=gff3")
    assert expected == core.generate_url("FAKE", config)


def test_generate_url_with_api_key():
    """Test URL generation for API key"""
    config = core.Config(api_key='FAKE')
    expected = "{}?{}".format(ENTREZ_URL, "retmode=text&id=FAKE&db=nucleotide&api_key=FAKE&rettype=gbwithparts")
    assert expected == core.generate_url("FAKE", config)

    config.format = 'gff3'
    expected = "{}?{}".format(SVIEWER_URL, "retmode=text&id=FAKE&db=nucleotide&api_key=FAKE&report=gff3")
    assert expected == core.generate_url("FAKE", config)
