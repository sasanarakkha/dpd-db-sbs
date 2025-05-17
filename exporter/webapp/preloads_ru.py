from sqlalchemy.orm import Session

from db.models import DpdHeadword, Lookup


def make_headwords_clean_set_ru(db_session: Session) -> set[str]:
    """Make a set of Pāḷi headwords and English and Russian meanings."""

    # add headwords
    results = db_session.query(DpdHeadword).all()
    headwords_clean_set = set([i.lemma_clean for i in results])

    # add all english and russian meanings
    results = db_session.query(Lookup).filter(Lookup.epd != "").filter(Lookup.rpd != "").all()
    headwords_clean_set.update([i.lookup_key for i in results])

    return headwords_clean_set

