"""Tests for the core module."""

from argparse import Namespace
import pytest
import requests_mock

from ncbi_acc_download import core


@pytest.yield_fixture
def req():
    """Get requests_mock into the pytest infrastructure."""
    with requests_mock.mock() as req:
        yield req


def test_config():
    """Test the config class."""
    args = Namespace(molecule="nucleotide", verbose=False)
    config = core.Config.from_args(args)
    assert config.verbose is False
    assert config.molecule == 'nucleotide'


def test_download_from_ncbi(req, tmpdir):
    """Test downloading things from NCBI."""
    req.get(core.NCBI_URL, text='This works.')
    outdir = tmpdir.mkdir('outdir')
    filename = outdir.join('foo')
    expected = outdir.join('foo.gbk')
    config = core.Config(molecule='nucleotide', verbose=False)

    core.download_from_ncbi('FOO', config, filename=filename)

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

    params = core._build_params(dl_id, config)

    assert params == expected_params

    expected_params = {
        'tool': 'ncbi-acc-download',
        'retmode': 'text',
        'rettype': 'fasta',
        'id': 'TEST',
        'db': 'protein'
    }
    config.molecule = 'protein'

    params = core._build_params(dl_id, config)

    assert params == expected_params


def test_generate_filename():
    """Test output file name generation."""
    params = dict(id='TEST', db='nucleotide')

    filename = core._generate_filename(params, 'foo')
    assert filename == 'foo.gbk'

    params['db'] = 'protein'
    filename = core._generate_filename(params, None)
    assert filename == 'TEST.fa'

