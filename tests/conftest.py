import pytest
import requests_mock


@pytest.fixture
def req():
    """Get requests_mock into the pytest infrastructure."""
    with requests_mock.mock() as req:
        yield req
