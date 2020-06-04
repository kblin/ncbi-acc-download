"""Record validation logic."""

import logging
# If Biopython is not available, all checks will return False
try:
    from Bio import SeqIO
    from Bio.SeqFeature import BeforePosition, AfterPosition
    HAVE_BIOPYTHON = True
except ImportError:  # pragma: no cover
    HAVE_BIOPYTHON = False


VALIDATION_LEVELS = {'none', 'loads', 'all', 'correct'}


def run_extended_validation(handle, file_format, validation_level):
    """Check if the dowloaded sequence file can load."""
    if not HAVE_BIOPYTHON:
        return False
    # we wrote to the handle, so rewind it
    handle.seek(0)
    try:
        processed_seq = False
        records = []
        for rec in SeqIO.parse(handle, file_format):
            processed_seq = True
            if validation_level == 'loads':
                continue
            if validation_level == 'correct':
                ## Correct possible errors from downloaded a restricted-range genbank file
                ## Will write over the downloaded file
                newfeats = []
                for f in rec.features:
                    try:
                        if not isinstance(f.location.start, BeforePosition) and not isinstance(f.location.end, AfterPosition):
                            newfeats.append(f)
                    except AttributeError:
                        newfeats.append(f)
                rec.features = newfeats
                records.append(rec)
        if not processed_seq:
            logging.error('no seq')

        if validation_level == 'correct':
            ## rewrite StringIO data
            handle.truncate(0)
            handle.seek(0)
            SeqIO.write(records, handle, 'genbank')
        return processed_seq
    except (ValueError, AssertionError) as err:
        logging.error(err)
        return False
    except Exception as err:
        logging.error("Unhandled exception %s while parsing sequence file.", err)
        return False
