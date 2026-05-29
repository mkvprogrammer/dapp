"""
Шифрует секретный ключ аккаунта пользователя при помощи пароля пользователя
для безопасного хранения в БД
"""

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.exceptions import (
    InvalidWalletPasswordError,
    WalletKeyNotConfiguredError,
)

def _derive_key(password: str) -> bytes:
    """Генерирует детерминированный крипто-ключ из текстового пароля пользователя."""
    # Для учебного проекта используем фиксированную соль, чтобы всегда расшифровывать одним паролем
    salt = b"university_dapp_fixed_salt_123" 
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_key(private_key_hex: str, password: str) -> str:
    """Шифрует приватный ключ кошелька паролем пользователя."""
    key = _derive_key(password)
    f = Fernet(key)
    # Возвращаем зашифрованную строку для сохранения в БД
    return f.encrypt(private_key_hex.encode()).decode()


def decrypt_key(encrypted_key_str: str, password: str) -> str:
    """Низкоуровневая расшифровка (без доменных исключений)."""
    key = _derive_key(password)
    f = Fernet(key)
    return f.decrypt(encrypted_key_str.encode()).decode()


def decrypt_wallet_private_key(encrypted_key_str: str | None, password: str) -> str:
    """
    Расшифровывает приватный ключ кошелька с переводом ошибок в доменные исключения.

    Используется в HTTP-ручках без try/except: глобальный handler сопоставит статус-код.
    """
    if not encrypted_key_str:
        raise WalletKeyNotConfiguredError()
    try:
        return decrypt_key(encrypted_key_str, password)
    except InvalidToken as exc:
        raise InvalidWalletPasswordError() from exc
