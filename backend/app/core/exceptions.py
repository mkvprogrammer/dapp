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


class OrganizerWalletNotConfiguredError(DomainException):
    """У организатора не настроен зашифрованный приватный ключ кошелька."""


class InvalidWalletPasswordError(DomainException):
    """Неверный пароль для расшифровки приватного ключа кошелька."""