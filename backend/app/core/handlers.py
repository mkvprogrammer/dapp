"""
Глобальные обработчики исключений FastAPI.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AlreadyEnrolledError,
    AuctionClosedError,
    AuctionNotFoundError,
    AuctionTimeError,
    BlockchainCommunicationError,
    BidNotFoundError,
    DatabasePersistenceError,
    DomainException,
    InsufficientTokensError,
    NotEnrolledInProjectError,
    ProjectAccessDeniedError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidWalletPasswordError,
    WalletKeyNotConfiguredError,
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
    if isinstance(exc, WalletKeyNotConfiguredError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Wallet private key is not configured for this account"},
        )
    if isinstance(exc, InvalidWalletPasswordError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid password for wallet decryption"},
        )
    if isinstance(exc, DatabasePersistenceError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to persist application data"},
        )
    if isinstance(exc, AuctionNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Auction not found"},
        )
    if isinstance(exc, AuctionClosedError):
        return JSONResponse(
            status_code=400,
            content={"detail": "This auction is already closed or cancelled"},
        )
    if isinstance(exc, AuctionTimeError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid lesson start time or duration"},
        )
    if isinstance(exc, BidNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Bid not found"},
        )
    if isinstance(exc, InsufficientTokensError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Insufficient university token balance"},
        )
    if isinstance(exc, NotEnrolledInProjectError):
        return JSONResponse(
            status_code=403,
            content={"detail": "You must be enrolled in the project to create an auction"},
        )
    if isinstance(exc, ProjectAccessDeniedError):
        return JSONResponse(
            status_code=403,
            content={"detail": "You do not have access to this project"},
        )

    # Любая другая ошибка домена
    return JSONResponse(
        status_code=422,
        content={"detail": "Business logic error"},
    )
