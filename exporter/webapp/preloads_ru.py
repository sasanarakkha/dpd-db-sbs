import re
from sqlalchemy.orm import Session, defer

from db.models import DpdHeadword, Lookup


def make_headwords_clean_set_ru(db_session: Session) -> set[str]:
    """Make a set of Pāḷi headwords and English and Russian meanings."""

    # add headwords
    # Optimization: Query only lemma_1 column to save memory
    results = db_session.query(DpdHeadword.lemma_1).all()
    headwords_clean_set = set([re.sub(r" \d.*$", "", i[0]) for i in results])

    # add all english and russian meanings
    # Optimization: Query only lookup_key column to save memory
    results_epd = db_session.query(Lookup.lookup_key).filter(Lookup.epd != "").all()
    headwords_clean_set.update([i.lookup_key for i in results_epd])

    results_rpd = db_session.query(Lookup.lookup_key).filter(Lookup.rpd != "").all()
    headwords_clean_set.update([i.lookup_key for i in results_rpd])

    return headwords_clean_set

