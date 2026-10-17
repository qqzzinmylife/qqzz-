from sqlalchemy.orm import Session

from app.modules.customer import repository
from app.modules.customer.models import Customer


def find_bound_customer(db: Session, user_id: int) -> Customer | None:
    """按登录身份找已绑定的客户档案。"""
    return repository.find_bound_by_user_id(db, user_id)


def find_bound_customer_id(db: Session, user_id: int) -> int | None:
    customer = find_bound_customer(db, user_id)
    return customer.id if customer is not None else None
