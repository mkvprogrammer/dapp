"""
Глобальные обработчики исключений FastAPI.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DomainException,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)


async def domain_exception_handler(
    request: Request,
    exc: DomainException,
) -> JSONResponse:
    """Переводит доменные исключения в HTTP-ответы."""
    if isinstance(exc, UserAlreadyExistsError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Student ID already registered"},
        )
    if isinstance(exc, InvalidCredentialsError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Incorrect student ID or password"},
        )
    if isinstance(exc, InvalidRefreshTokenError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid, expired or revoked refresh token"},
        )

    # Любая другая ошибка домена
    return JSONResponse(
        status_code=422,
        content={"detail": "Business logic error"},
    )
