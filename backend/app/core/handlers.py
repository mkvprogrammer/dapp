"""
Глобальные обработчики исключений FastAPI.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AlreadyEnrolledError,
    BlockchainCommunicationError,
    DatabasePersistenceError,
    DomainException,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidWalletPasswordError,
    OrganizerWalletNotConfiguredError,
    ProjectInactiveError,
    ProjectNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
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
    if isinstance(exc, UserNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "User not found"},
        )
    if isinstance(exc, ProjectNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Project not found"},
        )
    if isinstance(exc, AlreadyEnrolledError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Student is already enrolled in this project"},
        )
    if isinstance(exc, ProjectInactiveError):
        return JSONResponse(
            status_code=400,
            content={"detail": "This project is currently inactive"},
        )
    if isinstance(exc, BlockchainCommunicationError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Blockchain network node is temporarily unavailable"},
        )
    if isinstance(exc, OrganizerWalletNotConfiguredError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Organizer wallet key is not configured"},
        )
    if isinstance(exc, InvalidWalletPasswordError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid organizer password for wallet decryption"},
        )
    if isinstance(exc, DatabasePersistenceError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to persist application data"},
        )

    # Любая другая ошибка домена
    return JSONResponse(
        status_code=422,
        content={"detail": "Business logic error"},
    )
