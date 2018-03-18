"""Tests for the validation functions."""

from io import StringIO

from ncbi_acc_download import validate


def test_run_extended_validation_no_biopython(monkeypatch):
    """Test extended validation returns False if Biopython is not available."""
    monkeypatch.setattr(validate, 'HAVE_BIOPYTHON', False)
    handle = StringIO(u'>foo\nATGC\n>bar\nATGTGA\n')
    assert validate.run_extended_validation(handle, 'fasta', 'all') is False


def test_run_extended_validation_raises(monkeypatch, mocker):
    """Test the "seqence loads" validator catches exceptions in SeqIO.parse()."""
    seqio_mock = mocker.MagicMock()
    seqio_mock.parse = mocker.MagicMock(side_effect=ValueError)
    monkeypatch.setattr(validate, 'SeqIO', seqio_mock)
    assert validate.run_extended_validation(StringIO(u''), None, 'all') is False

    seqio_mock.parse = mocker.MagicMock(side_effect=Exception)
    assert validate.run_extended_validation(StringIO(u''), None, 'all') is False


def test_run_extended_validation_loads():
    """Test the "sequence loads" validator."""
    handle = StringIO(u'>foo\nATGC\n>bar\nATGTGA\n')
    assert validate.run_extended_validation(handle, 'fasta', 'loads')

    handle = StringIO(u'')
    assert validate.run_extended_validation(handle, 'fasta', 'loads') is False
