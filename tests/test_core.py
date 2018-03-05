"""Tests for the core module."""


from argparse import Namespace
import requests
import requests_mock

from ncbi_acc_download import core


def test_config():
    """Test the config class."""
    args = Namespace(molecule="nucleotide", verbose=False)
    config = core.Config.from_args(args)
    assert config.verbose is False
    assert config.molecule == 'nucleotide'

