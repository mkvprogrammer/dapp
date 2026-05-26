"""
Импорт всех ORM-моделей — нужен Alembic (autogenerate) и приложению.
"""

from app.models.token import RefreshToken
from app.models.user import User

__all__ = ["User", "RefreshToken"]
