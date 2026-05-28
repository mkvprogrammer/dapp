# backend/scripts/check_roles.py
import os
import sys
import json
from pathlib import Path
from web3 import Web3

# 1. НАСТРОЙКА ПУТЕЙ И ОКРУЖЕНИЯ
# Поднимаемся на уровень выше, чтобы найти корень backend и файл infra/.env
SCRIPT_DIR = Path(__file__).resolve().parent
print(SCRIPT_DIR)
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

INFRA_ENV_FILE = PROJECT_ROOT / "infra" / ".env"
DEPLOYED_JSON = PROJECT_ROOT /  "smartcontracts" / "deployed.json"
ARTIFACTS_DIR = PROJECT_ROOT / "smartcontracts" / "artifacts" / "contracts"

CONTRACT_NAME = "AuctionManager"

# Загружаем переменные из infra/.env вручную для независимости скрипта
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
    registry_address = deployed_data["contracts"][CONTRACT_NAME]

# 2. ЗАГРУЗКА ABI КОНТРАКТА
abi_path = ARTIFACTS_DIR / f"{CONTRACT_NAME}.sol" / f"{CONTRACT_NAME}.json"
if not abi_path.exists():
    print(f"❌ Ошибка: Скомпилированный артефакт {abi_path} не найден!")
    sys.exit(1)

with open(abi_path, "r", encoding="utf-8") as f:
    registry_abi = json.load(f)["abi"]


def check_roles(target_address: str):
    """Подключается к сети и проверяет все роли для указанного адреса."""
    # Приводим адрес к правильному шестнадцатеричному регистру (Checksum Address)
    try:
        target_address = Web3.to_checksum_address(target_address)
    except ValueError:
        print("❌ Ошибка: Невалидный формат Ethereum-адреса!")
        return

    # Подключаемся к ноде
    blockchain_url = os.getenv("BLOCKCHAIN_URL", "http://127.0.0.1:8541")
    w3 = Web3(Web3.HTTPProvider(blockchain_url))
    
    # Внедряем PoA мидлварь (критично для вашей сети!)
    from web3.middleware import geth_poa_middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not w3.is_connected():
        print(f"❌ Ошибка: Не удалось подключиться к блокчейн-ноде по адресу {blockchain_url}")
        return

    # Инициализируем контракт
    contract = w3.eth.contract(address=registry_address, abi=registry_abi)

    print(f"🌐 Подключено к сети: {blockchain_url}")
    print(f"📜 Контракт реестра: {registry_address}")
    print(f"🔎 Проверяю адрес: {target_address}\n")
    print("-" * 50)

    # 3. ЗАПРОС ХЭШЕЙ РОЛЕЙ ИЗ БЛОКЧЕЙНА
    try:
        admin_role_hash = contract.functions.DEFAULT_ADMIN_ROLE().call()
        organizer_role_hash = contract.functions.ORGANIZER_ROLE().call()
        if CONTRACT_NAME == "AuctionManager":
            user_role_hash = contract.functions.USER_ROLE().call()
    except Exception as e:
        print(f"❌ Ошибка при чтении констант ролей из контракта: {e}")
        return

    # 4. ПРОВЕРКА НАЛИЧИЯ РОЛЕЙ У КОШЕЛЬКА (hasRole)
    is_admin = contract.functions.hasRole(admin_role_hash, target_address).call()
    is_organizer = contract.functions.hasRole(organizer_role_hash, target_address).call()
    if CONTRACT_NAME == "AuctionManager":
        is_student = contract.functions.hasRole(user_role_hash, target_address).call()
    else:
        is_student = False

    # Выводим красивый отчет
    print(f"Для контракта {CONTRACT_NAME}, у указанного аккаунта следующие роли:")
    print(f"👑 Роль ADMIN (DEFAULT_ADMIN_ROLE):  {'✅ ДА' if is_admin else '❌ НЕТ'}")
    print(f"👨‍🏫 Роль TEACHER (ORGANIZER_ROLE):  {'✅ ДА' if is_organizer else '❌ НЕТ'}")
    print(f"🎓 Роль STUDENT (USER_ROLE):       {'✅ ДА' if is_student else '❌ НЕТ'}")
    print("-" * 50)


if __name__ == "__main__":
    # Скрипт ожидает адрес аргументом в консоли, либо спросит его вручную
    if len(sys.argv) > 1:
        address_to_check = sys.argv[1]
    else:
        address_to_check = input("Введите Ethereum-адрес для проверки ролей: ").strip()

    check_roles(address_to_check)
