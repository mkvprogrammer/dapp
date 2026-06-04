"""
Глобальные обработчики исключений FastAPI.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.validation_errors import format_validation_errors

from app.core.exceptions import (
    AlreadyEnrolledError,
    AuctionClosedError,
    AuctionNotFoundError,
    AuctionTimeError,
    BlockchainCommunicationError,
    BidAmountTooLowError,
    BidNotFoundError,
    DatabasePersistenceError,
    DomainException,
    InsufficientTokensError,
    NotEnrolledInProjectError,
    ProjectAccessDeniedError,
    AttendanceAlreadyProcessedError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    InvalidWalletPasswordError,
    StudentNotInAuctionError,
    WalletKeyNotConfiguredError,
    ProjectInactiveError,
    ProjectNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Ошибки Pydantic → понятный detail на русском (для фронта)."""
    return JSONResponse(
        status_code=422,
        content={"detail": format_validation_errors(exc)},
    )


async def domain_exception_handler(
    request: Request,
    exc: DomainException,
) -> JSONResponse:
    """Переводит доменные исключения в HTTP-ответы."""
    if isinstance(exc, UserAlreadyExistsError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Пользователь с таким ITMO ID уже зарегистрирован"},
        )
    if isinstance(exc, InvalidCredentialsError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Неверный ITMO ID или пароль"},
        )
    if isinstance(exc, InvalidRefreshTokenError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Сессия истекла или недействительна. Войдите снова"},
        )
    if isinstance(exc, UserNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Пользователь не найден"},
        )
    if isinstance(exc, ProjectNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Проект не найден"},
        )
    if isinstance(exc, AlreadyEnrolledError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Вы уже записаны на этот проект"},
        )
    if isinstance(exc, ProjectInactiveError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Проект сейчас неактивен"},
        )
    if isinstance(exc, BlockchainCommunicationError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Блокчейн-нода временно недоступна. Попробуйте позже"},
        )
    if isinstance(exc, WalletKeyNotConfiguredError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Кошелёк не настроен для этого аккаунта"},
        )
    if isinstance(exc, InvalidWalletPasswordError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Неверный пароль для расшифровки кошелька"},
        )
    if isinstance(exc, DatabasePersistenceError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Не удалось сохранить данные. Попробуйте позже"},
        )
    if isinstance(exc, AuctionNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Аукцион не найден"},
        )
    if isinstance(exc, AuctionClosedError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Аукцион уже завершён или отменён"},
        )
    if isinstance(exc, AuctionTimeError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Некорректное время или длительность занятия"},
        )
    if isinstance(exc, BidNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Ставка не найдена"},
        )
    if isinstance(exc, InsufficientTokensError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Недостаточно токенов на балансе"},
        )
    if isinstance(exc, BidAmountTooLowError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Сумма ставки меньше минимальной для этого аукциона"},
        )
    if isinstance(exc, NotEnrolledInProjectError):
        return JSONResponse(
            status_code=403,
            content={"detail": exc.detail},
        )
    if isinstance(exc, ProjectAccessDeniedError):
        return JSONResponse(
            status_code=403,
            content={"detail": "Нет доступа к этому проекту"},
        )
    if isinstance(exc, StudentNotInAuctionError):
        return JSONResponse(
            status_code=400,
            content={"detail": "У студента нет активной ставки в этом аукционе"},
        )
    if isinstance(exc, AttendanceAlreadyProcessedError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Посещение по этой ставке уже обработано"},
        )

    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка выполнения операции"},
    )
