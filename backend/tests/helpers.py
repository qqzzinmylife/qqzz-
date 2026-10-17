from sqlalchemy import func, select
from sqlalchemy.orm import Session


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def count_rows(db: Session, model) -> int:
    return db.execute(select(func.count()).select_from(model)).scalar_one()
