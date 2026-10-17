import pytest

from app.core.deps import require_bound_customer, require_merchant
from app.core.errors import AppError, ErrorCode
from app.modules.auth.models import User
from app.modules.customer.models import Customer


def _make_user(db, *, role: str, openid: str) -> User:
    user = User(openid=openid, role=role, status="active")
    db.add(user)
    db.flush()
    return user


def test_require_merchant_rejects_customer(db_session):
    user = _make_user(db_session, role="customer", openid="openid-not-merchant")

    with pytest.raises(AppError) as exc:
        require_merchant(user=user)

    assert exc.value.code is ErrorCode.FORBIDDEN


def test_require_bound_customer_returns_bound_customer(db_session):
    user = _make_user(db_session, role="customer", openid="openid-bound")
    customer = Customer(name="张三", user_id=user.id, bind_status="bound")
    db_session.add(customer)
    db_session.flush()

    assert require_bound_customer(user=user, db=db_session).id == customer.id


def test_require_bound_customer_rejects_unbound_user(db_session):
    user = _make_user(db_session, role="customer", openid="openid-unbound")

    with pytest.raises(AppError) as exc:
        require_bound_customer(user=user, db=db_session)

    assert exc.value.code is ErrorCode.CUSTOMER_NOT_BOUND


def test_require_bound_customer_rejects_merchant(db_session):
    user = _make_user(db_session, role="merchant", openid="openid-merchant-only")

    with pytest.raises(AppError) as exc:
        require_bound_customer(user=user, db=db_session)

    assert exc.value.code is ErrorCode.FORBIDDEN
