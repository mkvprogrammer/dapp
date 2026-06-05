"""
Pydantic-схемы P2P-переводов токенов.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TransferCreate(BaseModel):
    """Тело запроса на перевод токенов другому участнику проекта."""

    recipient_student_id: str = Field(..., min_length=1, max_length=50, description="ID студента-получателя")
    project_id: int = Field(..., description="Проект, в рамках которого переводятся токены")
    amount: Decimal = Field(..., gt=0, description="Сумма перевода")
    comment: str | None = Field(None, max_length=500, description="Комментарий к переводу")
    password: str = Field(..., min_length=1, description="Пароль для расшифровки ключа и подписи tx")


class TransferResponse(BaseModel):
    """Результат успешного перевода."""

    id: UUID = Field(..., description="ID записи перевода")
    project_id: int = Field(..., description="ID проекта")
    sender_student_id: str = Field(..., description="ID отправителя")
    recipient_student_id: str = Field(..., description="ID получателя")
    recipient_full_name: str = Field(..., description="ФИО получателя")
    amount: Decimal = Field(..., description="Сумма")
    comment: str | None = Field(None, description="Комментарий")
    status: str = Field(..., description="Статус: completed и др.")
    tx_hash: str | None = Field(None, description="Хэш onchain-транзакции")
    created_at: datetime = Field(..., description="Время перевода")


class TransferListItem(BaseModel):
    """Элемент истории переводов."""

    id: UUID = Field(..., description="ID перевода")
    direction: str = Field(..., description="in — входящий, out — исходящий")
    counterparty_name: str = Field(..., description="ФИО контрагента")
    counterparty_student_id: str = Field(..., description="ID контрагента")
    amount: Decimal = Field(..., description="Сумма")
    comment: str | None = Field(None, description="Комментарий")
    status: str = Field(..., description="Статус перевода")
    created_at: datetime = Field(..., description="Дата")


class TransferListResponse(BaseModel):
    """Пагинированная история переводов."""

    items: list[TransferListItem] = Field(..., description="Переводы")
    total: int = Field(..., description="Общее число по фильтру")


class RecentRecipient(BaseModel):
    """Недавний получатель для быстрого выбора."""

    user_id: UUID = Field(..., description="UUID получателя")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")


class RecentRecipientsResponse(BaseModel):
    """Список недавних получателей."""

    items: list[RecentRecipient] = Field(..., description="Получатели")


class WalletBalanceResponse(BaseModel):
    """Краткий ответ баланса кошелька."""

    available: Decimal = Field(..., description="Доступный баланс")
    project_id: int | None = Field(None, description="ID проекта (null — суммарно)")
