"""
Ядро интеграции с блокчейном (Web3 provider + контракты).

Важно:
- web3.py синхронный, поэтому в async-методах используется `asyncio.to_thread`,
  чтобы не блокировать event loop FastAPI.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Final

from eth_account import Account
from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from web3.providers import HTTPProvider
from web3.types import ChecksumAddress

from app.core.config import PROJECT_ROOT, settings

ARTIFACTS_DIR: Final[Path] = (
    PROJECT_ROOT / "smartcontracts" / "artifacts" / "contracts"
)
DEPLOYED_JSON_PATH: Final[Path] = PROJECT_ROOT / "smartcontracts" / "deployed.json"


def _load_contract_abi(contract_name: str) -> list[dict[str, Any]]:
    """
    Динамически грузит ABI из Hardhat-артефакта:
    `smartcontracts/artifacts/contracts/{Name}.sol/{Name}.json`.
    """
    artifact_path = ARTIFACTS_DIR / f"{contract_name}.sol" / f"{contract_name}.json"
    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Hardhat-артефакт не найден: {artifact_path}. "
            "Сначала выполните: cd smartcontracts && npm i && npx hardhat compile"
        )
    with artifact_path.open(encoding="utf-8") as f:
        artifact: dict[str, Any] = json.load(f)
    abi = artifact.get("abi")
    if not isinstance(abi, list):
        raise ValueError(f"В артефакте {artifact_path} отсутствует поле 'abi'")
    return abi


def _load_deployed_addresses() -> dict[str, str]:
    """Читает `smartcontracts/deployed.json` и возвращает map имя->адрес."""
    if not DEPLOYED_JSON_PATH.is_file():
        raise FileNotFoundError(
            f"Файл деплоя не найден: {DEPLOYED_JSON_PATH}. "
            "Сначала задеплойте контракты (см. smartcontracts/scripts)."
        )
    with DEPLOYED_JSON_PATH.open(encoding="utf-8") as f:
        deployed: dict[str, Any] = json.load(f)
    contracts = deployed.get("contracts")
    if not isinstance(contracts, dict):
        raise ValueError("Некорректный deployed.json: нет поля contracts")
    # Приводим к строкам на всякий случай
    return {str(k): str(v) for k, v in contracts.items()}


class BlockchainService:
    """
    Singleton-сервис Web3.

    Инициализация выполняется один раз при старте приложения (на импорт модуля
    или при явном создании экземпляра).
    """

    w3: Web3
    admin_address: ChecksumAddress
    token_contract: Contract
    registry_contract: Contract
    auction_contract: Contract

    def __init__(self) -> None:
        # Lock сериализует отправку tx от одного admin-адреса и защищает nonce от гонок.
        self._tx_lock = asyncio.Lock()

        # 1) Web3 provider
        self.w3 = Web3(HTTPProvider(settings.blockchain_url))

        # 2) Middleware для PoA (Clique): фиксит extraData/nonce заголовка блока
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # 3) Вычисляем публичный адрес админа из приватного ключа
        # Приватный ключ может прийти как с "0x", так и без — Account.from_key принимает оба варианта
        admin_acct = Account.from_key(settings.BLOCKCHAIN_ADMIN_PRIVATE_KEY)
        self.admin_address = Web3.to_checksum_address(admin_acct.address)

        # 4) ABI + deployed addresses + контракт-объекты
        deployed = _load_deployed_addresses()

        token_addr = deployed.get("UniversityToken")
        registry_addr = deployed.get("ProjectRegistry")
        auction_addr = deployed.get("AuctionManager")
        if not token_addr or not registry_addr or not auction_addr:
            raise ValueError(
                "В deployed.json отсутствуют адреса UniversityToken/ProjectRegistry/AuctionManager"
            )

        token_abi = _load_contract_abi("UniversityToken")
        registry_abi = _load_contract_abi("ProjectRegistry")
        auction_abi = _load_contract_abi("AuctionManager")

        self.token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_addr),
            abi=token_abi,
        )
        self.registry_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(registry_addr),
            abi=registry_abi,
        )
        self.auction_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(auction_addr),
            abi=auction_abi,
        )

    async def _send_admin_tx(self, func: Any) -> str:
        """
        Строит и отправляет транзакцию от лица админа.

        Здесь важные моменты:
        - gasPrice=0 (как в вашем docker-compose PoA, где майнеры gasprice=0)
        - nonce берём из сети
        - подписываем приватным ключом админа и отправляем raw tx
        """

        def _sync_send() -> str:
            # Берём nonce из `pending`, чтобы учитывать уже отправленные, но ещё не замайненные tx.
            nonce = self.w3.eth.get_transaction_count(self.admin_address, block_identifier="pending")
            chain_id = int(self.w3.eth.chain_id)

            # Сначала собираем "черновик" транзакции, затем оцениваем gas.
            tx: dict[str, Any] = func.build_transaction(
                {
                    "from": self.admin_address,
                    "nonce": nonce,
                    "gasPrice": 0,
                    "chainId": chain_id,
                    "value": 0,
                }
            )
            if "gas" not in tx:
                # Оценка газа может падать при revert — это тоже полезный сигнал для диагностики.
                tx["gas"] = int(func.estimate_gas({"from": self.admin_address}))

            signed = self.w3.eth.account.sign_transaction(
                tx, private_key=settings.BLOCKCHAIN_ADMIN_PRIVATE_KEY
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            return tx_hash.hex()

        async with self._tx_lock:
            return await asyncio.to_thread(_sync_send)

    async def _get_role(self, contract: Contract, role_fn_name: str) -> bytes:
        """
        Достаёт bytes32 роли из контракта: например `USER_ROLE()` или `ORGANIZER_ROLE()`.

        Вызов `.call()` синхронный, поэтому выполняем в отдельном потоке.
        """

        def _sync_call() -> bytes:
            fn = getattr(contract.functions, role_fn_name)
            return fn().call()

        return await asyncio.to_thread(_sync_call)

    async def _grant_role(self, contract: Contract, role: bytes, wallet_address: str) -> str:
        """Выдаёт роль через стандартный AccessControl.grantRole(role, account)."""
        addr = Web3.to_checksum_address(wallet_address)
        func = contract.functions.grantRole(role, addr)
        return await self._send_admin_tx(func)

    async def _revoke_role(self, contract: Contract, role: bytes, wallet_address: str) -> str:
        """Отзывает роль через стандартный AccessControl.revokeRole(role, account)."""
        addr = Web3.to_checksum_address(wallet_address)
        func = contract.functions.revokeRole(role, addr)
        return await self._send_admin_tx(func)

    async def grant_organizer_role_onchain(self, wallet_address: str) -> str:
        """
        Выдаёт роль ORGANIZER в контракте реестра через `grantRole`.

        Контракт ожидает bytes32 role. Обычно это константа `ORGANIZER_ROLE()`.
        """
        # ORGANIZER_ROLE есть во всех 3 контрактах (ProjectRegistry, UniversityToken, AuctionManager)
        role_registry = await self._get_role(self.registry_contract, "ORGANIZER_ROLE")
        role_token = await self._get_role(self.token_contract, "ORGANIZER_ROLE")
        role_auction = await self._get_role(self.auction_contract, "ORGANIZER_ROLE")

        # Выдаём роль в каждом контракте (три отдельные tx)
        tx1 = await self._grant_role(self.registry_contract, role_registry, wallet_address)
        await self._grant_role(self.token_contract, role_token, wallet_address)
        await self._grant_role(self.auction_contract, role_auction, wallet_address)
        return tx1

    async def revoke_organizer_role_onchain(self, wallet_address: str) -> str:
        """Отзывает роль ORGANIZER через `revokeRole`."""
        role_registry = await self._get_role(self.registry_contract, "ORGANIZER_ROLE")
        role_token = await self._get_role(self.token_contract, "ORGANIZER_ROLE")
        role_auction = await self._get_role(self.auction_contract, "ORGANIZER_ROLE")

        tx1 = await self._revoke_role(self.registry_contract, role_registry, wallet_address)
        await self._revoke_role(self.token_contract, role_token, wallet_address)
        await self._revoke_role(self.auction_contract, role_auction, wallet_address)
        return tx1

    async def grant_student_role_onchain(self, wallet_address: str) -> str:
        """
        Выдача роли USER_ROLE при регистрации.

        В вашей архитектуре USER_ROLE существует только в `AuctionManager`,
        а в `ProjectRegistry` и `UniversityToken` её нет — поэтому там мы лишь
        гарантируем отсутствие ORGANIZER_ROLE (на всякий случай).
        """
        # 1) В AuctionManager выдаём USER_ROLE
        user_role = await self._get_role(self.auction_contract, "USER_ROLE")
        tx_hash = await self._grant_role(self.auction_contract, user_role, wallet_address)

        # 2) В остальных контрактах "студенческой" роли нет: просто снимаем ORGANIZER_ROLE
        # (если вдруг адрес ранее был организатором).
        await self.revoke_organizer_role_onchain(wallet_address)

        return tx_hash

    async def sync_roles_for_user(self, wallet_address: str, target: str) -> None:
        """
        Унифицированная синхронизация ролей по всем контрактам.

        target:
        - "user": USER_ROLE в AuctionManager, без ORGANIZER_ROLE в остальных
        - "organizer": ORGANIZER_ROLE во всех трёх (и USER_ROLE опционально)
        - "none": снимаем все прикладные роли
        """
        if target == "user":
            await self.grant_student_role_onchain(wallet_address)
            return
        if target == "organizer":
            # Организатору также логично иметь USER_ROLE (createAuction допускает либо USER_ROLE, либо ORGANIZER_ROLE),
            # но ORGANIZER_ROLE уже достаточно. Выдадим USER_ROLE для полноты.
            user_role = await self._get_role(self.auction_contract, "USER_ROLE")
            await self._grant_role(self.auction_contract, user_role, wallet_address)
            await self.grant_organizer_role_onchain(wallet_address)
            return
        if target == "none":
            # Снимаем ORGANIZER_ROLE везде и USER_ROLE в AuctionManager
            await self.revoke_organizer_role_onchain(wallet_address)
            user_role = await self._get_role(self.auction_contract, "USER_ROLE")
            await self._revoke_role(self.auction_contract, user_role, wallet_address)
            return
        raise ValueError(f"Unknown role target: {target}")

    async def _send_signed_tx(self, private_key: str, func: Any) -> str:
        """
        Строит и отправляет транзакцию от лица произвольного кошелька (создатель / студент / организатор).

        Используется для createProject, createAuction, placeBid и т.д.
        """

        def _sync_send() -> str:
            account = Account.from_key(private_key)
            sender = Web3.to_checksum_address(account.address)
            nonce = self.w3.eth.get_transaction_count(sender, block_identifier="pending")
            chain_id = int(self.w3.eth.chain_id)

            tx: dict[str, Any] = func.build_transaction(
                {
                    "from": sender,
                    "nonce": nonce,
                    "gasPrice": 0,
                    "chainId": chain_id,
                    "value": 0,
                }
            )
            if "gas" not in tx:
                tx["gas"] = int(func.estimate_gas({"from": sender}))

            signed = self.w3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            return tx_hash.hex()

        async with self._tx_lock:
            return await asyncio.to_thread(_sync_send)

    async def create_project_onchain(
        self,
        owner_private_key: str,
        name: str,
        refund_rate_bps: int,
        penalty_schedule: list[int],
    ) -> tuple[int, str]:
        """
        Создаёт проект в ProjectRegistry от лица организатора.

        Возвращает (blockchain_id, tx_hash).
        """
        if len(penalty_schedule) != 4:
            raise ValueError("penalty_schedule must contain exactly 4 values")

        penalty_tuple = tuple(int(x) for x in penalty_schedule)
        func = self.registry_contract.functions.createProject(
            name,
            int(refund_rate_bps),
            penalty_tuple,
        )
        tx_hash = await self._send_signed_tx(owner_private_key, func)

        def _parse_project_id() -> int:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.get("status") != 1:
                raise ValueError(f"createProject transaction reverted: {tx_hash}")

            logs = self.registry_contract.events.ProjectCreated().process_receipt(receipt)
            if not logs:
                raise ValueError(f"ProjectCreated event not found in receipt: {tx_hash}")
            return int(logs[0]["args"]["projectId"])

        blockchain_id = await asyncio.to_thread(_parse_project_id)
        return blockchain_id, tx_hash

    async def mint_tokens(
        self,
        wallet_address: str,
        blockchain_id: int,
        amount: int,
    ) -> str:
        """
        Минтит ERC-1155 токены проекта студенту от лица DEFAULT_ADMIN_ROLE (бэкенд-админ).
        """
        to_addr = Web3.to_checksum_address(wallet_address)
        func = self.token_contract.functions.mint(
            to_addr,
            int(blockchain_id),
            int(amount),
            b"",
        )
        return await self._send_admin_tx(func)

    def get_project_info(self, project_id: int) -> dict[str, Any]:
        """Синхронный .call() к контракту за данными проекта (для будущих фич)."""
        raise NotImplementedError

    async def _ensure_token_approval_for_auction(self, owner_private_key: str) -> str | None:
        """
        Проверяет setApprovalForAll для AuctionManager.

        Если одобрения нет — строит, подписывает и отправляет транзакцию approve.
        Возвращает tx_hash одобрения или None, если уже было одобрено.
        """
        account = Account.from_key(owner_private_key)
        owner = Web3.to_checksum_address(account.address)
        auction_addr = self.auction_contract.address

        def _is_approved() -> bool:
            return bool(
                self.token_contract.functions.isApprovedForAll(owner, auction_addr).call()
            )

        if await asyncio.to_thread(_is_approved):
            return None

        # build_transaction → sign_transaction → send_raw_transaction
        approve_func = self.token_contract.functions.setApprovalForAll(auction_addr, True)
        return await self._send_signed_tx(owner_private_key, approve_func)

    async def get_token_balance(self, wallet_address: str, project_blockchain_id: int) -> int:
        """Синхронный balanceOf для ERC-1155 (projectId = token id)."""
        owner = Web3.to_checksum_address(wallet_address)

        def _call() -> int:
            return int(
                self.token_contract.functions.balanceOf(owner, int(project_blockchain_id)).call()
            )

        return await asyncio.to_thread(_call)

    async def create_auction_onchain(
        self,
        project_blockchain_id: int,
        resource_name: str,
        duration_seconds: int,
        lesson_start_ts: int,
        resource_limit: int,
        creator_private_key: str,
    ) -> tuple[int, str]:
        """
        createAuction в AuctionManager.

        Подписант (creator_private_key) — любой аккаунт с USER_ROLE или ORGANIZER_ROLE
        (студент, записанный на курс, или организатор). Не используется ключ админа бэкенда.

        Возвращает (blockchain_auction_id, tx_hash).
        """
        func = self.auction_contract.functions.createAuction(
            int(project_blockchain_id),
            resource_name,
            int(duration_seconds),
            int(lesson_start_ts),
            int(resource_limit),
        )
        tx_hash = await self._send_signed_tx(creator_private_key, func)

        def _parse_auction_id() -> int:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.get("status") != 1:
                raise ValueError(f"createAuction reverted: {tx_hash}")
            logs = self.auction_contract.events.AuctionCreated().process_receipt(receipt)
            if not logs:
                raise ValueError(f"AuctionCreated event not found: {tx_hash}")
            return int(logs[0]["args"]["auctionId"])

        auction_id = await asyncio.to_thread(_parse_auction_id)
        return auction_id, tx_hash

    async def place_bid_onchain(
        self,
        blockchain_auction_id: int,
        amount: int,
        student_private_key: str,
    ) -> str:
        """
        Две onchain-операции студента:
        1) setApprovalForAll (если нужно)
        2) placeBid(auctionId, amount)
        """
        await self._ensure_token_approval_for_auction(student_private_key)

        bid_func = self.auction_contract.functions.placeBid(
            int(blockchain_auction_id),
            int(amount),
        )
        return await self._send_signed_tx(student_private_key, bid_func)

    async def cancel_bid_onchain(
        self,
        blockchain_auction_id: int,
        student_private_key: str,
    ) -> str:
        """cancelBid в AuctionManager от лица студента."""
        func = self.auction_contract.functions.cancelBid(int(blockchain_auction_id))
        return await self._send_signed_tx(student_private_key, func)

    async def get_leaderboard(
        self,
        blockchain_auction_id: int,
        limit: int,
    ) -> list[tuple[str, int]]:
        """
        getLeaderboard из контракта: список (address, bid_amount).
        """
        def _call() -> list[tuple[str, int]]:
            users, bids = self.auction_contract.functions.getLeaderboard(
                int(blockchain_auction_id),
                int(limit),
            ).call()
            return [(Web3.to_checksum_address(u), int(b)) for u, b in zip(users, bids)]

        return await asyncio.to_thread(_call)

    async def is_student_in_guaranteed_top(
        self,
        blockchain_auction_id: int,
        wallet_address: str,
    ) -> bool:
        """Синхронный view-вызов isStudentInGuaranteedTop."""
        addr = Web3.to_checksum_address(wallet_address)

        def _call() -> bool:
            return bool(
                self.auction_contract.functions.isStudentInGuaranteedTop(
                    int(blockchain_auction_id),
                    addr,
                ).call()
            )

        return await asyncio.to_thread(_call)


# Singleton-экземпляр (инициализируется один раз)
blockchain_service = BlockchainService()
