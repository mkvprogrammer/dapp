"""
Сервис авторизации: регистрация, вход и обновление JWT (без HTTP-слоя).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from eth_account import Account
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.blockchain import blockchain_service
from app.core.config import settings
from app.core.crypto import encrypt_key 
from app.core.exceptions import (
  InvalidCredentialsError,
  InvalidRefreshTokenError,
  UserAlreadyExistsError,
  BlockchainCommunicationError
)
from app.core.security import (
  create_access_token,
  create_refresh_token,
  get_password_hash,
  verify_password,
)
from app.models.token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import UserLogin, UserRegister


class TokenPair(TypedDict):
  access_token: str
  refresh_token: str

logger = logging.getLogger(__name__)


def _hash_refresh_token(token: str) -> str:
  """SHA-256 хэш refresh-токена для хранения в БД (не храним сырой токен)."""
  return hashlib.sha256(token.encode()).hexdigest()


def _token_payload(user: User) -> dict[str, str]:
  """Payload JWT: ID пользователя и роль."""
  return {"sub": str(user.id), "role": user.role.value}


async def register_user(db: AsyncSession, schema: UserRegister) -> tuple[User, str]:
  """
  Регистрирует студента: кошелёк, шифрование ключа, USER_ROLE onchain, запись в БД.

  Возвращает пользователя и сырой приватный ключ (отдаётся клиенту один раз).
  """
  # 1. Проверка уникальности student_id
  result = await db.execute(
    select(User).where(User.student_id == schema.student_id)
  )
  if result.scalar_one_or_none() is not None:
    raise UserAlreadyExistsError()

  # 2. Хэширование пароля
  password_hash = get_password_hash(schema.password)

  # 3. Генерация Ethereum-кошелька (в БД сохраняем только публичный адрес)
  account = Account.create()
  raw_private_key = account.key.hex() # Чистый приватник для возврата на фронтенд

  # 4. ШИФРОВАНИЕ: шифруем приватник ЧИСТЫМ паролем пользователя
  encrypted_key = encrypt_key(raw_private_key, schema.password)

  # 5–6. Создание и сохранение пользователя
  user = User(
    student_id=schema.student_id,
    full_name=schema.full_name,
    password_hash=password_hash,
    wallet_address=account.address,
    encrypted_private_key=encrypted_key,
    role=UserRole.STUDENT,
  )
  db.add(user)
  # await db.commit()
  # await db.refresh(user)
  try:
    # Отправляем транзакцию в сеть localPoA
    # Важно: USER_ROLE существует только в AuctionManager, поэтому сервис блокчейна
    # сам корректно синхронизирует роли по всем контрактам.
    await blockchain_service.sync_roles_for_user(user.wallet_address, target="user")
    
    # Только если блокчейн ответил успехом — фиксируем изменения в PostgreSQL
    await db.commit()
    await db.refresh(user)
  except Exception as blockchain_error:
    # Если нода недоступна или транзакция отклонена
    await db.rollback() # Отменяем запись в БД
    logger.exception("On-chain role sync failed during user registration")
    raise BlockchainCommunicationError() from blockchain_error

  return user, raw_private_key


async def authenticate_user(db: AsyncSession, schema: UserLogin) -> User:
  """Проверяет student_id и пароль; обновляет last_login_at."""
  result = await db.execute(
    select(User).where(User.student_id == schema.student_id)
  )
  user = result.scalar_one_or_none()

  if user is None or not verify_password(schema.password, user.password_hash):
    raise InvalidCredentialsError()

  user.last_login_at = datetime.now(UTC)
  await db.commit()
  await db.refresh(user)
  return user


async def create_jwt_tokens(db: AsyncSession, user: User) -> TokenPair:
  """Выпускает access/refresh JWT и сохраняет хэш refresh-токена в БД."""
  payload = _token_payload(user)

  # 1. Выпуск пары JWT
  access_token = create_access_token(payload)
  refresh_token = create_refresh_token(payload)

  # 2. Сохранение хэша refresh-токена в БД
  expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
  db.add(
    RefreshToken(
      user_id=user.id,
      token_hash=_hash_refresh_token(refresh_token),
      expires_at=expires_at,
    )
  )
  await db.commit()

  return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenPair:
  """Ротация refresh-токена: отзыв старого, выпуск новой пары JWT."""
  token_hash = _hash_refresh_token(refresh_token)
  now = datetime.now(UTC)

  # 1. Поиск записи по хэшу
  result = await db.execute(
    select(RefreshToken).where(RefreshToken.token_hash == token_hash)
  )
  stored = result.scalar_one_or_none()

  # 2. Валидация: существует, не отозван, не истёк
  if (
    stored is None
    or stored.is_revoked
    or stored.expires_at <= now
  ):
    raise InvalidRefreshTokenError()

  # 3. Отзыв старого токена (rotation)
  stored.is_revoked = True

  user_result = await db.execute(select(User).where(User.id == stored.user_id))
  user = user_result.scalar_one()

  return await create_jwt_tokens(db, user)


async def logout_user(db: AsyncSession, refresh_token: str) -> None:
    """
    Отзывает (аннулирует) refresh-токен пользователя в базе данных.
    """
    # 1. Хэшируем полученный токен для поиска в БД
    token_hash = _hash_refresh_token(refresh_token)
    
    # 2. Ищем токен в таблице refresh_tokens
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored_token = result.scalar_one_or_none()
    
    # 3. Если токен найден и еще не отозван — отзываем его
    if stored_token and not stored_token.is_revoked:
        stored_token.is_revoked = True
        await db.commit()
    # Если токен не найден или уже отозван, мы просто молча завершаем функцию.
    # Это хорошая практика для logout (idempotency), чтобы не спамить ошибками.
