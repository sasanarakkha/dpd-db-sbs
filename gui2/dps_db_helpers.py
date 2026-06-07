from sqlalchemy.orm.session import Session
from db.models import Russian, SBS


def fetch_ru(db_session: Session, headword_id: int) -> Russian | None:
    """Fetch Russian word from db."""
    return db_session.query(Russian).filter(Russian.id == headword_id).first()


def fetch_sbs(db_session: Session, headword_id: int) -> SBS | None:
    """Fetch SBS word from db."""
    return db_session.query(SBS).filter(SBS.id == headword_id).first()
