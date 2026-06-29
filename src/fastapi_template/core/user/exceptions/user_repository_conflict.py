from fastapi_template.core.user.exceptions.user import UserError


class UserRepositoryConflictError(UserError):
    """Define UserRepositoryConflictError."""
