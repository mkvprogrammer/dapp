# backend/scripts/get_token_balance.py
import os
import sys
import json
from pathlib import Path
from web3 import Web3

# 1. НАСТРОЙКА ПУТЕЙ И ОКРУЖЕНИЯ
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

INFRA_ENV_FILE = PROJECT_ROOT / "infra" / ".env"
DEPLOYED_JSON = PROJECT_ROOT / "smartcontracts" / "deployed.json"
ARTIFACTS_DIR = PROJECT_ROOT / "smartcontracts" / "artifacts" / "contracts"

# Загружаем переменные из infra/.env
if INFRA_ENV_FILE.exists():
    with open(INFRA_ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

# Читаем адреса из deployed.json
if not DEPLOYED_JSON.exists():
    print(f"❌ Ошибка: Файл {DEPLOYED_JSON} не найден. Сначала выполните деплой!")
    sys.exit(1)

with open(DEPLOYED_JSON, "r", encoding="utf-8") as f:
    deployed_data = json.load(f)
    token_address = deployed_data["contracts"]["UniversityToken"]

# 2. ЗАГРУЗКА ABI КОНТРАКТА UNIVERSITYTOKEN
abi_path = ARTIFACTS_DIR / "UniversityToken.sol" / "UniversityToken.json"
if not abi_path.exists():
    print(f"❌ Ошибка: Скомпилированный артефакт {abi_path} не найден!")
    sys.exit(1)

with open(abi_path, "r", encoding="utf-8") as f:
    token_abi = json.load(f)["abi"]


def get_balance(target_address: str, project_id: int):
    """Запрашивает у контракта ERC-1155 баланс токенов для конкретного projectId."""
    # Приводим адрес к правильному шестнадцатеричному регистру
    try:
        target_address = Web3.to_checksum_address(target_address)
    except ValueError:
        print("❌ Ошибка: Невалидный формат Ethereum-адреса!")
        return

    # Подключаемся к ноде localPoA
    blockchain_url = os.getenv("BLOCKCHAIN_URL", "http://127.0.0.1:8541")
    w3 = Web3(Web3.HTTPProvider(blockchain_url))
    
    # Внедряем PoA мидлварь (обязательно для вашей сети)
    from web3.middleware import geth_poa_middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not w3.is_connected():
        print(f"❌ Ошибка: Не удалось подключиться к блокчейн-ноде {blockchain_url}")
        return

    # Инициализируем контракт токена
    contract = w3.eth.contract(address=token_address, abi=token_abi)

    print(f"🌐 Сеть: {blockchain_url}")
    print(f"🪙 Контракт токена (ERC-1155): {token_address}")
    print(f"🔎 Проверяемый кошелек: {target_address}")
    print(f"📚 ID Проекта (Token ID): {project_id}\n")
    print("-" * 60)

    try:
        # В стандарте ERC-1155 функция проверки баланса называется balanceOf(account, id)
        # В качестве id токена выступает blockchain_id (номер проекта)
        balance = contract.functions.balanceOf(target_address, project_id).call()
        
        print(f"📊 Текущий баланс токенов в блокчейне: 💰 {balance} UT")
    except Exception as e:
        print(f"❌ Ошибка при вызове balanceOf в блокчейне: {e}")
    
    print("-" * 60)


if __name__ == "__main__":
    # Скрипт может принимать аргументы из консоли, либо спросит их вручную
    if len(sys.argv) > 2:
        address = sys.argv[1]
        proj_id = int(sys.argv[2])
    else:
        address = input("Введите Ethereum-адрес кошелька: ").strip()
        proj_id = int(input("Введите ID проекта (число): ").strip())

    get_balance(address, proj_id)
