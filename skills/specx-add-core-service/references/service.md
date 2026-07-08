# Specx Service Reference

Services own focused reusable core behavior. Delivery-only helpers such as
auth dependencies, rate limiting, and request-context adapters live under
`delivery/`, not `core/<scope>/services/`.

## Class Shape

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.foundation.service import BaseService


@dataclass(kw_only=True, slots=True)
class OrderPricingService(BaseService):
    """Service that prices orders from items and tax policy.

    Example:
        total = service.price(items=(OrderItem(price=Money("10.00")),))
    """

    _tax_policy_service: Injected[TaxPolicyService]

    def price(self, *, items: tuple[OrderItem, ...]) -> Money:
        subtotal = sum((item.price for item in items), Money.zero())
        tax = self._tax_policy_service.calculate_tax(amount=subtotal)
        return subtotal + tax
```

Use `BaseService` and `Injected[...]` for dependencies. Keep methods
keyword-only. Every service class name must end with `Service`.

## Dependency Choice

Inject a concrete class when:

- it is project-owned;
- it has no external IO;
- there is one implementation;
- tests can use it deterministically.

An in-memory dependency is acceptable as a concrete core service only when it is
deliberately part of the application behavior or a starter/demo implementation
with no external IO. Name it honestly with the `Service` suffix, for example
`OrderSummaryStoreService` or `StaticCatalogService`, and keep it under
`services/` only while it has no database, network, filesystem, Redis, clock, or
randomness dependency. Move it behind a core port and infrastructure adapter as
soon as it becomes external IO.

Inject a core port/ABC when:

- it wraps external IO;
- it hides a framework or SDK;
- it has multiple real implementations;
- replacing it in tests is important.

## UoW Parameters

Services may receive an active UoW as a method argument:

```python
@dataclass(kw_only=True, slots=True)
class UserCredentialCheckingService(BaseService):
    """Service that checks user credentials inside an active UoW.

    Example:
        user = await service.authenticate(uow=uow, email=email, password=password)
    """

    _password_hashing_service: Injected[PasswordHashingService]

    async def authenticate(
        self,
        *,
        uow: UnitOfWork,
        email: str,
        password: str,
    ) -> User | None:
        user = await uow.users.find_by_email(email=email)
        if user is None:
            return None
        password_valid = self._password_hashing_service.verify(
            raw_password=password,
            password_hash=user.password_hash,
        )
        if not password_valid:
            return None
        return user
```

The service does not open `async with uow`. The use case owns the transaction.

## Unit Tests

Construct services directly unless DI behavior is the subject:

```python
def test_order_pricer_adds_tax() -> None:
    service = OrderPricingService(
        _tax_policy_service=FixedTaxPolicyService(rate=Decimal("0.20")),
    )

    result = service.price(items=(OrderItem(price=Money("10.00")),))

    assert result == Money("12.00")
```

## Avoid

- No `Manager`, `Helper`, `Utils`, or vague `Handler` names.
- No framework imports.
- No SQLAlchemy/Redis/HTTP clients.
- No transaction scopes.
- No direct environment reads.
- No bare service classes.
- No service class without the `Service` suffix.
