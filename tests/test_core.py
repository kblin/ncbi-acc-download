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

