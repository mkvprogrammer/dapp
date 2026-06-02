# Пробелы API: вёрстка vs backend

Документ для реализации недостающих ручек. Схемы — черновик под `backend/app/schemas/`, согласован с существующими `auth.py`, `project.py`, `auction.py`, `admin.py`.

---

## Сводка

| Область | Реализовано | Не хватает |
|---------|-------------|------------|
| Auth | register, login, logout, refresh, me | расширенный профиль, last_login |
| Dashboard | — | агрегат главной |
| Wallet / балансы | только `token_balance` при enroll | сводка, frozen, pending |
| Projects | list all, detail, create, enroll | my projects, members, join-by-code, filters |
| Attendance | — | коды, redeem, stats |
| Organizer | create project | stats, mint, charts |
| Auctions | CRUD + bid + leaderboard | filters, bid-history, расширенные поля, SSE |
| Transfers | — | весь модуль |
| Notifications | — | весь модуль |
| Admin | change role | users list, audit, emergency, health |
| Files | — | upload image |

---

## 1. Dashboard (`home.html`)

### `GET /api/v1/dashboard`
**Auth:** Bearer JWT  
**Назначение:** одним запросом данные для главной (приветствие, stat cards, превью).

```python
# app/schemas/dashboard.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class DashboardProjectPreview(BaseModel):
    project_id: int
    name: str
    token_balance: Decimal
    active_auctions_count: int
    activity_percent: int = Field(..., ge=0, le=100)


class DashboardAuctionPreview(BaseModel):
    auction_id: int
    resource_name: str
    project_id: int
    project_name: str
    status: str
    my_bid_amount: Decimal | None = None
    my_rank: int | None = None
    participants_count: int
    end_time: datetime
    image_url: str | None = None


class DashboardActivityPreview(BaseModel):
    id: UUID
    type: str  # auction | transfer | attendance | ...
    title: str
    description: str
    amount_delta: Decimal | None = None
    created_at: datetime


class DashboardResponse(BaseModel):
    total_balance: Decimal
    active_auctions_count: int
    projects_count: int
    wins_this_month: int
    unread_notifications_count: int
    projects: list[DashboardProjectPreview]
    active_auctions: list[DashboardAuctionPreview]
    recent_activity: list[DashboardActivityPreview]
```

---

## 2. Профиль и кошелёк (`profile.html`)

### Расширение модели `User` (миграция Alembic)
Нужны поля, которых нет в ORM сегодня:

```python
# app/models/user.py — добавить
email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
faculty: Mapped[str | None] = mapped_column(String(200), nullable=True)
last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### `GET /api/v1/users/me/profile`
**Auth:** Bearer JWT

```python
# app/schemas/user.py
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserStatsResponse(BaseModel):
    won_auctions: int
    auction_participations: int
    tokens_earned: Decimal
    confirmed_attendance_hours: Decimal


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(validation_alias="id")
    student_id: str
    full_name: str
    email: EmailStr | None = None
    faculty: str | None = None
    wallet_address: str
    role: str
    stats: UserStatsResponse
    created_at: datetime
```

### `PATCH /api/v1/users/me/profile`

```python
class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=150)
    email: EmailStr | None = None
    faculty: str | None = Field(None, max_length=200)
```

### `GET /api/v1/users/me/balances`
**Auth:** Bearer JWT  
**UI:** «Общий баланс», «Доступно / Заморожено / Ожидает возврата».

```python
class ProjectBalanceItem(BaseModel):
    project_id: int
    project_name: str
    available: Decimal
    frozen: Decimal      # locked в активных ставках
    pending_refund: Decimal


class UserBalancesResponse(BaseModel):
    total: Decimal
    available: Decimal
    frozen: Decimal
    pending_refund: Decimal
    by_project: list[ProjectBalanceItem]
```

> `frozen` = сумма `Bid.amount` со статусом `locked` по проекту.  
> `pending_refund` = ставки в процессе возврата после закрытия аукциона.

### `GET /api/v1/users/me/activity`
**Query:** `limit: int = 20`, `offset: int = 0`

```python
class ActivityType(str, Enum):
    AUCTION_BID = "auction_bid"
    AUCTION_WIN = "auction_win"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ATTENDANCE = "attendance"
    MINT = "mint"


class ActivityItem(BaseModel):
    id: UUID
    type: ActivityType
    title: str
    description: str
    project_id: int | None = None
    project_name: str | None = None
    amount_delta: Decimal | None = None
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityItem]
    total: int
```

### `GET /api/v1/users/me/auctions/active`
**UI:** блок «Мои активные аукционы» на profile/home.

```python
class MyActiveAuctionItem(BaseModel):
    auction_id: int
    resource_name: str
    project_name: str
    my_bid_amount: Decimal
    my_rank: int
    participants_count: int
    end_time: datetime
    time_left_seconds: int


class MyActiveAuctionsResponse(BaseModel):
    items: list[MyActiveAuctionItem]
```

---

## 3. Проекты (`projects.html`, `project-details.html`)

### `GET /api/v1/users/me/projects`
**Auth:** Bearer JWT  
**Отличие от `GET /projects/`:** только проекты, где есть запись в `user_projects`.

**Query:**
- `search: str | None`
- `is_active: bool | None = True` — «Активные / Архив»
- `sort: Literal["activity", "balance", "name", "enrolled_at"] = "activity"`

```python
class MyProjectListItem(BaseModel):
    id: int
    name: str
    description: str
    token_balance: Decimal
    auctions_count: int
    activity_percent: int = Field(..., ge=0, le=100)
    is_active: bool
    organizer_name: str
    enrolled_at: datetime


class MyProjectsListResponse(BaseModel):
    items: list[MyProjectListItem]
    total_balance: Decimal
    stats: dict[str, int]  # active_projects, total_auction_participations, wins
```

### `GET /api/v1/projects/{project_id}/members`
**Auth:** Bearer JWT (organizer/admin или участник проекта)

**Query:** `search: str | None`, `limit: int = 50`, `offset: int = 0`

```python
class ProjectMemberItem(BaseModel):
    user_id: UUID
    student_id: str
    full_name: str
    token_balance: Decimal
    attendance_count: int
    auctions_participated: int
    enrolled_at: datetime


class ProjectMembersResponse(BaseModel):
    project_id: int
    items: list[ProjectMemberItem]
    total: int
```

### `GET /api/v1/projects/{project_id}/balance`
**Auth:** Bearer JWT (текущий пользователь)

```python
class ProjectBalanceResponse(BaseModel):
    project_id: int
    available: Decimal
    frozen: Decimal
    pending_refund: Decimal
```

### `POST /api/v1/projects/join-by-code`
**Auth:** Bearer JWT, role `student`

```python
class ProjectJoinByCodeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)


class ProjectJoinByCodeResponse(BaseModel):
    project_id: int
    project_name: str
    token_balance: Decimal
    enrolled_at: datetime
    tx_hash: str | None = None
```

### Расширение `ProjectDetailResponse`

```python
class OrganizerInfo(BaseModel):
    user_id: UUID
    full_name: str
    student_id: str
    email: EmailStr | None = None


class ProjectDetailResponseExtended(ProjectDetailResponse):
    organizer: OrganizerInfo
    members_count: int
    my_balance: Decimal | None = None
    my_attendance_percent: int | None = None
    active_auctions_count: int
    semester_label: str | None = None  # опционально, из description или отдельного поля
```

---

## 4. Посещения (`project-details`, `organizer.html`)

### Модели (новые таблицы)

```python
# app/models/attendance.py (черновик)
class AttendanceCode(Base):
    id: UUID
    project_id: int
    code: str          # "MATH-7K2P"
    label: str         # "Лекция · Мат. анализ"
    expires_at: datetime
    created_by: UUID
    is_active: bool

class AttendanceRecord(Base):
    id: UUID
    project_id: int
    user_id: UUID
    code_id: UUID
    tokens_minted: Decimal
    created_at: datetime
```

### `POST /api/v1/projects/{project_id}/attendance-codes`
**Auth:** organizer проекта

```python
class AttendanceCodeCreate(BaseModel):
    label: str = Field(..., min_length=3, max_length=200)
    duration_minutes: int = Field(default=90, ge=5, le=480)
    tokens_reward: Decimal = Field(default=Decimal("5"), gt=0)
    password: str  # подпись mint on-chain


class AttendanceCodeResponse(BaseModel):
    id: UUID
    code: str
    label: str
    expires_at: datetime
    tokens_reward: Decimal
```

### `GET /api/v1/projects/{project_id}/attendance-codes/active`
**Auth:** organizer

```python
class ActiveAttendanceCodeResponse(BaseModel):
    id: UUID
    code: str
    label: str
    expires_at: datetime
    redemptions_count: int
```

### `POST /api/v1/projects/{project_id}/attendance/redeem`
**Auth:** student, enrolled in project

```python
class AttendanceRedeemRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)


class AttendanceRedeemResponse(BaseModel):
    project_id: int
    tokens_minted: Decimal
    new_balance: Decimal
    tx_hash: str
```

### `GET /api/v1/projects/{project_id}/attendance/stats`
**Auth:** organizer или участник

```python
class AttendanceStatsResponse(BaseModel):
    project_id: int
    average_attendance_percent: int
    total_sessions: int
    my_visits: int | None = None  # для студента
```

---

## 5. Организатор (`organizer.html`)

### `GET /api/v1/projects/{project_id}/organizer/stats`
**Auth:** organizer проекта или admin

```python
class WeeklyMintBar(BaseModel):
    week_label: str
    amount: Decimal


class DailyAuctionBar(BaseModel):
    weekday: str
    bids_count: int


class OrganizerStatsResponse(BaseModel):
    project_id: int
    project_name: str
    semester_label: str | None
    members_count: int
    members_trend_month: int
    tokens_in_circulation: Decimal
    tokens_trend_week: Decimal
    active_auctions_count: int
    average_attendance_percent: int
    attendance_trend_month: int
    weekly_mints: list[WeeklyMintBar]
    auction_activity_by_day: list[DailyAuctionBar]
```

### `POST /api/v1/projects/{project_id}/members/{user_id}/mint-tokens`
**Auth:** organizer

```python
class MintTokensRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    reason: str | None = Field(None, max_length=500)
    password: str


class MintTokensResponse(BaseModel):
    user_id: UUID
    project_id: int
    amount: Decimal
    new_balance: Decimal
    tx_hash: str
```

---

## 6. Переводы (`transfers.html`)

### Модель

```python
# app/models/transfer.py
class Transfer(Base):
    id: UUID
    project_id: int
    sender_id: UUID
    recipient_id: UUID
    amount: Decimal
    comment: str | None
    status: str  # pending | completed | failed
    tx_hash: str | None
    created_at: datetime
```

### `GET /api/v1/wallet/balance`
**Auth:** JWT  
**Query:** `project_id: int | None` — если None, агрегат по всем проектам.

```python
class WalletBalanceResponse(BaseModel):
    available: Decimal
    project_id: int | None = None
```

### `POST /api/v1/transfers`
**Auth:** student

```python
class TransferCreate(BaseModel):
    recipient_student_id: str = Field(..., min_length=3, max_length=50)
    project_id: int
    amount: Decimal = Field(..., gt=0)
    comment: str | None = Field(None, max_length=500)
    password: str


class TransferResponse(BaseModel):
    id: UUID
    project_id: int
    sender_student_id: str
    recipient_student_id: str
    recipient_full_name: str
    amount: Decimal
    comment: str | None
    status: str
    tx_hash: str | None
    created_at: datetime
```

### `GET /api/v1/transfers`
**Query:** `project_id`, `direction: in|out|all`, `limit`, `offset`

```python
class TransferListItem(BaseModel):
    id: UUID
    direction: Literal["in", "out"]
    counterparty_name: str
    counterparty_student_id: str
    amount: Decimal
    comment: str | None
    status: str
    created_at: datetime


class TransferListResponse(BaseModel):
    items: list[TransferListItem]
    total: int
```

### `GET /api/v1/transfers/recent-recipients`

```python
class RecentRecipient(BaseModel):
    user_id: UUID
    student_id: str
    full_name: str


class RecentRecipientsResponse(BaseModel):
    items: list[RecentRecipient]
```

### `GET /api/v1/transfers/export`
**Query:** `format=csv`, те же фильтры что у list  
**Response:** `StreamingResponse` (не JSON).

---

## 7. Уведомления (`notifications.html`)

### Модель

```python
class NotificationType(str, Enum):
    BID_OUTBID = "bid_outbid"
    AUCTION_ENDING = "auction_ending"
    TRANSFER_SENT = "transfer_sent"
    TRANSFER_RECEIVED = "transfer_received"
    ATTENDANCE_CONFIRMED = "attendance_confirmed"
    MEMBER_JOINED = "member_joined"
    ATTENDANCE_CODE_EXPIRING = "attendance_code_expiring"
    ORGANIZER = "organizer"


class Notification(Base):
    id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    body: str
    meta: dict  # JSONB: project_id, auction_id, bid_amount, ...
    is_read: bool
    created_at: datetime
```

### `GET /api/v1/notifications`
**Query:**
- `type: NotificationType | None`
- `unread_only: bool = False`
- `limit: int = 50`, `offset: int = 0`

```python
class NotificationMeta(BaseModel):
    project_id: int | None = None
    project_name: str | None = None
    auction_id: int | None = None
    bid_amount: Decimal | None = None
    rank: int | None = None
    balance_after: Decimal | None = None
    action_url: str | None = None


class NotificationItem(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    body: str
    meta: NotificationMeta
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread_count: int
```

### `PATCH /api/v1/notifications/{notification_id}/read`

```python
class NotificationReadResponse(BaseModel):
    id: UUID
    is_read: bool
```

### `PATCH /api/v1/notifications/read-all`

```python
class NotificationReadAllResponse(BaseModel):
    updated_count: int
```

---

## 8. Аукционы — расширения

### Расширение `GET /api/v1/auctions/` (query + response)

**Query (новые):**
```python
class AuctionListQuery(BaseModel):
    project_id: int | None = None
    status: Literal["open", "closed", "cancelled", "all"] = "open"
    search: str | None = None
    resource_type: str | None = None
    min_bid_lte: Decimal | None = None
    max_bid_gte: Decimal | None = None
```

**Расширенный `AuctionListResponse`:**
```python
class AuctionListResponseExtended(BaseModel):
    id: int
    project_id: int
    project_name: str
    resource_name: str
    resource_type: str | None = None
    resource_limit: int
    status: str
    start_time: datetime
    end_time: datetime
    current_top_bid: Decimal | None = None
    participants_count: int
    my_bid_amount: Decimal | None = None
    my_rank: int | None = None
    image_url: str | None = None
```

### `GET /api/v1/auctions/{auction_id}/bid-history`
**UI:** «История ставок» (хронология, не только leaderboard).

```python
class BidHistoryEntry(BaseModel):
    id: UUID
    student_id: str
    full_name: str
    amount: Decimal
    action: Literal["placed", "raised", "cancelled"]
    created_at: datetime


class BidHistoryResponse(BaseModel):
    auction_id: int
    entries: list[BidHistoryEntry]
```

### Расширение `AuctionCreate` / `AuctionDetailResponse`

```python
class ResourceType(str, Enum):
    CONSULTATION = "consultation"
    LECTURE = "lecture"
    ROOM = "room"
    EQUIPMENT = "equipment"


class AuctionCreateExtended(AuctionCreate):
    resource_type: ResourceType = ResourceType.CONSULTATION
    location: str | None = Field(None, max_length=200)
    description: str | None = None
    min_bid: Decimal = Field(default=Decimal("1"), gt=0)
    bid_step: Decimal = Field(default=Decimal("0.5"), gt=0)
    event_end_time: datetime | None = None
    rules_text: str | None = None
    image_url: str | None = None
    is_draft: bool = False


class AuctionDetailResponseExtended(AuctionDetailResponse):
    resource_type: str | None = None
    location: str | None = None
    description: str | None = None
    min_bid: Decimal | None = None
    bid_step: Decimal | None = None
    event_end_time: datetime | None = None
    rules_text: str | None = None
    image_url: str | None = None
    project_name: str
    participants_count: int
    current_top_bid: Decimal | None = None
```

### `GET /api/v1/auctions/{auction_id}/stream` (SSE, опционально)
**Auth:** Bearer (query `token` или cookie)  
**Events:** `leaderboard_update`, `time_tick`, `auction_closed`  
**Payload:** JSON `LeaderboardResponse` или `{ "seconds_left": int }`.

---

## 9. Загрузка файлов

### `POST /api/v1/uploads/images`
**Auth:** JWT  
**Content-Type:** `multipart/form-data`  
**Field:** `file` (PNG/JPG, max 2MB)

```python
class ImageUploadResponse(BaseModel):
    url: str
    filename: str
    size_bytes: int
```

---

## 10. Admin (`admin.html`)

### `GET /api/v1/admin/users`
**Auth:** admin

**Query:** `search: str | None`, `role: UserRole | None`, `limit`, `offset`

```python
class AdminUserListItem(BaseModel):
    user_id: UUID
    full_name: str
    student_id: str
    role: str
    projects_count: int
    last_login_at: datetime | None
    is_active: bool


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
```

### `GET /api/v1/admin/audit-log`

**Query:** `event_type: AuditEventType | None`, `limit`, `offset`

```python
class AuditEventType(str, Enum):
    AUCTION = "auction"
    USER = "user"
    TOKEN = "token"
    SYSTEM = "system"


class AuditLogEntry(BaseModel):
    id: UUID
    created_at: datetime
    actor_name: str
    actor_student_id: str | None
    action: str
    object_ref: str
    ip_address: str | None


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
```

### `POST /api/v1/admin/emergency-stop`

```python
class EmergencyStopRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    password: str  # подтверждение admin


class EmergencyStopResponse(BaseModel):
    stopped_auctions_count: int
    message: str
```

### `GET /api/v1/admin/health`

```python
class ServiceHealth(BaseModel):
    name: str
    status: Literal["ok", "warn", "error"]
    detail: str
    latency_ms: int | None = None


class AdminHealthResponse(BaseModel):
    services: list[ServiceHealth]
    active_auctions: int
    bids_per_hour: int
    blockchain_block_number: int | None
```

---

## 11. Wallet top-up (макет «Пополнить»)

> В prod-сценарии токены минтятся организатором / за посещение. Для демо можно:

### `POST /api/v1/wallet/demo-top-up` (только dev/staging)
**Auth:** student

```python
class DemoTopUpRequest(BaseModel):
    project_id: int
    amount: Decimal = Field(..., gt=0, le=100)


class DemoTopUpResponse(BaseModel):
    project_id: int
    new_balance: Decimal
```

---

## 12. Частично реализовано — что доработать без новых роутов

| Эндпоинт | Проблема | Доработка |
|----------|----------|-----------|
| `GET /projects/` | отдаёт все проекты, не «мои» | фронт фильтрует вручную; нужен `/users/me/projects` |
| `GET /auctions/` | нет `end_time`, `participants_count` в list | расширить `AuctionListResponse` |
| `GET /auth/me` | нет email, faculty, stats | расширить или `/users/me/profile` |
| `POST /projects/{id}/enroll` | enroll по ID, не по коду | UI «Присоединиться» ждёт join-by-code |
| `PUT /admin/users/{id}/role` | есть | нет list users для таблицы admin |

---

## 13. Приоритет реализации

1. **P0 (разблокирует UI):** `users/me/balances`, `users/me/projects`, расширение `auctions/` list, `auctions/{id}/bid-history`
2. **P1:** transfers, notifications, attendance codes
3. **P2:** dashboard aggregate, organizer stats, admin users/audit
4. **P3:** SSE, image upload, demo top-up, emergency stop

---

## 14. Роутер (план монтирования)

```python
# app/api/api.py — добавить
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
# projects.py — доп. routes: members, attendance, organizer
# admin.py — users, audit-log, emergency-stop, health
```
