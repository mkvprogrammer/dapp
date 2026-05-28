from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, BigInteger, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Project(Base):
    __tablename__ = "projects"

    # id соответствует projectId в контракте
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    organizer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # ID в смарт-контракте (BigInteger переводится в int в Python)
    blockchain_id: Mapped[int] = mapped_column(BigInteger, unique=True)  
    
    # Numeric транслируется в специальный тип Decimal в Python для точности денег
    refund_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="80.00")  
    
    # Для JSON полей используем тип Any или dict/list в аннотации
    penalty_schedule: Mapped[list[int]] = mapped_column(JSONB, server_default="[10, 20, 30, 50]")  
    initial_supply: Mapped[int] = mapped_column(Integer, server_default="1000")  
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ORM Связи (Relationships)
    users: Mapped[list[UserProject]] = relationship("UserProject", back_populates="project", cascade="all, delete-orphan")


class UserProject(Base):
    __tablename__ = "user_projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Балансы блокчейна (uint256) очень большие, используем Numeric(78, 0)
    token_balance: Mapped[Decimal] = mapped_column(Numeric(78, 0), server_default="0")  

    # ORM Связи (Relationships)
    project: Mapped[Project] = relationship("Project", back_populates="users")

    # Ограничение уникальности вынесено в __table_args__, имя uq_user_project 
    # будет автоматически перехвачено вашим convention словарем
    # я запрещает появление строк с одинаковой комбинацией значений 
    # в указанных колонках.
    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', name='uq_user_project'),
    )
