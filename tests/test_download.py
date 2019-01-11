from io import StringIO
import pytest
import requests

from ncbi_acc_download.core import Config
from ncbi_acc_download.errors import DownloadError
from ncbi_acc_download import download


def test_write_stream(mocker):
    req = mocker.Mock()
    req.iter_content = mocker.Mock(side_effect=requests.exceptions.ChunkedEncodingError)
    handle = StringIO()
    cfg = Config()

    with pytest.raises(DownloadError):
        download.write_stream(req, handle, "FAKE", cfg)
