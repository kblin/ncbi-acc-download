"""Record validation logic."""

import logging

# If Biopython is not available, all checks will return False
try:
    from Bio import SeqIO
    HAVE_BIOPYTHON = True
except ImportError:  # pragma: no cover
    HAVE_BIOPYTHON = False


VALIDATION_LEVELS = {'none', 'loads', 'all'}


def run_extended_validation(handle, file_format, validation_level):
    """Check if the dowloaded sequence file can load."""
    if not HAVE_BIOPYTHON:
        return False
    # we wrote to the handle, so rewind it
    handle.seek(0)
    try:
        processed_seq = False
        for rec in SeqIO.parse(handle, file_format):
            processed_seq = True
            if validation_level == 'loads':
                continue
        if not processed_seq:
            logging.error('no seq')
        return processed_seq
    except (ValueError, AssertionError) as err:
        logging.error(err)
        return False
    except Exception as err:
        logging.error("Unhandled exception %s while parsing sequence file.")
        return False
