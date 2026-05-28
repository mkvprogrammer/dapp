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