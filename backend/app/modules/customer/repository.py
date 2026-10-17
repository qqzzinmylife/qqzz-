from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.customer.models import Customer


def find_bound_by_user_id(db: Session, user_id: int) -> Customer | None:
    return db.execute(select(Customer).where(Customer.user_id == user_id)).scalar_one_or_none()
