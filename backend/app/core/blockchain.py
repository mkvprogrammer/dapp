"""
Модуль интеграции с локальной PoA-нодой и артефактами Hardhat.
"""

import json
from functools import lru_cache
from typing import Any

from web3 import Web3
from web3.providers import HTTPProvider

from app.core.config import PROJECT_ROOT, settings

# Корень артефактов Hardhat относительно корня репозитория
ARTIFACTS_DIR = PROJECT_ROOT / "smartcontracts" / "artifacts" / "contracts"


@lru_cache
def get_web3() -> Web3:
    """
    Возвращает настроенный синхронный экземпляр Web3 (HTTPProvider).

    URL RPC берётся из ``settings.blockchain_url`` (нода node1 в docker-compose).
    """
    provider = HTTPProvider(settings.blockchain_url)
    w3 = Web3(provider)
    return w3


def load_contract_abi(contract_name: str) -> list[dict[str, Any]]:
    """
    Загружает ABI контракта из скомпилированного Hardhat-артефакта.

    Путь: ``smartcontracts/artifacts/contracts/{Name}.sol/{Name}.json``.
    """
    artifact_path = (
        ARTIFACTS_DIR / f"{contract_name}.sol" / f"{contract_name}.json"
    )
    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Артефакт не найден: {artifact_path}. "
            "Выполните компиляцию: cd smartcontracts && npx hardhat compile"
        )

    with artifact_path.open(encoding="utf-8") as f:
        artifact: dict[str, Any] = json.load(f)

    abi = artifact.get("abi")
    if not isinstance(abi, list):
        raise ValueError(f"В артефакте {artifact_path} отсутствует поле 'abi'")

    return abi
