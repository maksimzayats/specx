# Specx Use Case Reference

Use cases coordinate externally meaningful application actions.

## Class Shape

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.users.dtos.register_user_result_dto import RegisterUserResultDTO
from order_service.core.users.repositories.user_unit_of_work import (
    UserUnitOfWorkManager,
)
from order_service.foundation.command import BaseCommand
from order_service.foundation.use_case import BaseUseCase


class RegisterUserCommand(BaseCommand):
    """Command for registering a user.

    Example:
        RegisterUserCommand(email="ada@example.com", password="secret")
    """

    email: str
    password: str


@dataclass(kw_only=True, slots=True)
class RegisterUserUseCase(BaseUseCase):
    """Use case that registers a user through the users transaction boundary.

    Example:
        result = await use_case.execute(
            command=RegisterUserCommand(
                email="ada@example.com",
                password="secret",
            ),
        )
    """

    _identity_normalizer_service: Injected[IdentityNormalizerService]
    _password_hashing_service: Injected[PasswordHashingService]
    _unit_of_work_manager: Injected[UserUnitOfWorkManager]

    async def execute(self, *, command: RegisterUserCommand) -> RegisterUserResultDTO:
        normalized = self._identity_normalizer_service.normalize(command=command)
        password_hash = self._password_hashing_service.hash_password(
            raw_password=normalized.password,
        )

        async with self._unit_of_work_manager as unit_of_work:
            existing_user = await unit_of_work.users.find_by_email(
                email=normalized.email,
            )
            if existing_user is not None:
                raise UserAlreadyExistsError

            user = await unit_of_work.users.create(
                email=normalized.email,
                password_hash=password_hash,
            )

        return RegisterUserResultDTO(user_id=user.id)
```

## Inputs And Results

Use `BaseCommand` for state-changing inputs, `BaseQuery` for read-only inputs,
and `BaseDTO` for results:

```python
from order_service.foundation.command import BaseCommand
from order_service.foundation.query import BaseQuery


class RegisterUserCommand(BaseCommand):
    """Command for registering a user.

    Example:
        RegisterUserCommand(email="ada@example.com", password="secret")
    """

    email: str
    password: str


class ListUsersQuery(BaseQuery):
    """Query for listing users.

    Example:
        ListUsersQuery()
    """
```

Define the command or query in the same file as the use case. Do not put
commands or queries under `dtos/`, and do not add a `DTO` suffix to them.
Define result DTOs under `core/<scope>/dtos/`, not inline with the use case.

Result DTO file:

```python
from order_service.foundation.dto import BaseDTO


class RegisterUserResultDTO(BaseDTO):
    """Result DTO returned after user registration.

    Example:
        RegisterUserResultDTO(user_id=1)
    """

    user_id: int
```

## Transaction Rules

- A use case does not need a UoW when all collaborators are deterministic
  core services and no external persistence is involved.
- Open at most one UoW scope inside `execute(...)`.
- Open the scope only when the use case needs transactional persistence.
- Commands may change state. Queries are read-only and should not call
  repository mutators such as `add`, `save`, `create`, `update`, or `delete`.
- Inject the scope `UnitOfWorkManager`, not `Provider[UnitOfWork]` and not an
  active UoW instance. The manager opens a fresh active UoW for each
  `execute(...)` call.
- Pass the active `uow` to services that need repositories.
- Do not let services open transactions.
- Do not commit, rollback, or close sessions outside the UoW implementation.
- Return DTOs from use cases. Do not return entities from `execute(...)`.
- If repositories return entities, map them to result DTOs inside the use case
  before returning.

## Exceptions

Put application exceptions under `exceptions/` or near the use case when
the error is local:

```python
from order_service.foundation.exceptions import BaseApplicationError


class UserAlreadyExistsError(BaseApplicationError):
    """Raised when registration would duplicate an email.

    Example:
        raise UserAlreadyExistsError
    """
```

Delivery translates these errors to HTTP responses.

## Unit Test Pattern

```python
from dataclasses import dataclass, field
from typing import Literal

from order_service.foundation.repository import BaseRepository
from order_service.foundation.unit_of_work import BaseUnitOfWork
from order_service.foundation.unit_of_work_manager import BaseUnitOfWorkManager


@dataclass(kw_only=True, slots=True)
class FakeUsersRepository(BaseRepository):
    """Fake users repository for use-case unit tests.

    Example:
        users = FakeUsersRepository(emails={"ada@example.com"})
    """

    emails: set[str] = field(default_factory=set)

    def _repository_marker(self) -> None:
        return None

    async def find_by_email(self, *, email: str) -> object | None:
        return object() if email in self.emails else None


class FakeUnitOfWork(BaseUnitOfWork):
    """Fake active UoW that exposes test repositories.

    Example:
        unit_of_work = FakeUnitOfWork(users=users)
    """

    def __init__(self, *, users: FakeUsersRepository) -> None:
        self.users = users

    def _unit_of_work_marker(self) -> None:
        return None


class FakeUnitOfWorkManager(BaseUnitOfWorkManager[FakeUnitOfWork]):
    """Fake manager that opens an active fake UoW for each test action.

    Example:
        async with FakeUnitOfWorkManager(users=users) as unit_of_work:
            await unit_of_work.users.find_by_email(email="ada@example.com")
    """

    def __init__(self, *, users: FakeUsersRepository) -> None:
        self._users = users
        self._unit_of_work: FakeUnitOfWork | None = None
        self.committed_count = 0
        self.rolled_back_count = 0

    async def __aenter__(self) -> FakeUnitOfWork:
        self._unit_of_work = FakeUnitOfWork(users=self._users)
        return self._unit_of_work

    async def __aexit__(self, exc_type, exc, traceback) -> Literal[False]:
        if self._unit_of_work is None:
            raise AssertionError("unit of work manager was not active")
        if exc_type is None:
            self.committed_count += 1
        else:
            self.rolled_back_count += 1
        self._unit_of_work = None
        return False


async def test_register_user_rejects_duplicate_email() -> None:
    users = FakeUsersRepository(emails={"ada@example.com"})
    use_case = RegisterUserUseCase(
        _identity_normalizer_service=IdentityNormalizerService(),
        _password_hashing_service=FakePasswordHashingService(),
        _unit_of_work_manager=FakeUnitOfWorkManager(users=users),
    )

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            command=RegisterUserCommand(
                email="ada@example.com",
                password="secret",
            ),
        )
```

## Avoid

- No framework request objects in method signatures.
- No delivery schemas in core.
- No entities returned from use cases.
- No SQLAlchemy/Redis/HTTP clients in core.
- No `container.resolve(...)`.
- No vague names such as `UserManager` or `OrderHandler`.
- No bare classes; inherit existing foundation bases or add a new foundation
  base only when a real class category needs it.
