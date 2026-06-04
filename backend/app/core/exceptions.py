"""
Доменные исключения бизнес-логики (без привязки к HTTP).
"""


class DomainException(Exception):
    """Базовый класс ошибок домена."""


class UserAlreadyExistsError(DomainException):
    """Студент с таким ID уже зарегистрирован."""


class InvalidCredentialsError(DomainException):
    """Неверный студент ID или пароль."""


class InvalidRefreshTokenError(DomainException):
    """Токен обновления не существует, отозван или истёк."""


class UserNotFoundError(DomainException):
    """Пользователь не найден."""


class BlockchainCommunicationError(DomainException):
    """Сбой при отправке транзакции в блокчейн-сеть."""


class ProjectNotFoundError(DomainException):
    """Проект с таким ID не найден."""


class AlreadyEnrolledError(DomainException):
    """Студент уже записан на этот проект."""


class ProjectInactiveError(DomainException):
    """Проект заморожен или неактивен."""


class DatabasePersistenceError(DomainException):
    """Не удалось сохранить или обновить данные в PostgreSQL."""


class WalletKeyNotConfiguredError(DomainException):
    """У пользователя не настроен зашифрованный приватный ключ кошелька."""


class OrganizerWalletNotConfiguredError(WalletKeyNotConfiguredError):
    """Алиас для обратной совместимости (создание проекта организатором)."""


class InvalidWalletPasswordError(DomainException):
    """Неверный пароль для расшифровки приватного ключа кошелька."""


class AuctionNotFoundError(DomainException):
    """Аукцион с таким ID не найден в системе."""


class AuctionClosedError(DomainException):
    """Попытка действия на завершённом или отменённом аукционе."""


class AuctionTimeError(DomainException):
    """Некорректные временные рамки аукциона."""


class BidNotFoundError(DomainException):
    """Ставка в запрашиваемом аукционе не найдена."""


class InsufficientTokensError(DomainException):
    """Недостаточно токенов на балансе для ставки."""


class BidAmountTooLowError(DomainException):
    """Сумма ставки меньше минимальной для аукциона."""


class NotEnrolledInProjectError(DomainException):
    """Пользователь не является участником проекта для запрошенного действия."""

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or "Вы не записаны на этот проект"
        super().__init__(self.detail)


class ProjectAccessDeniedError(DomainException):
    """Нет прав на действия с этим проектом."""


class StudentNotInAuctionError(DomainException):
    """У студента нет активной ставки в этом аукционе."""


class AttendanceAlreadyProcessedError(DomainException):
    """Посещение по этой ставке уже обработано."""