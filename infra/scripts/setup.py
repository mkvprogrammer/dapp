"""
Генерация аккаунтов и genesis.json для локальной PoA-сети на Clique.
"""

import json
from pathlib import Path
from typing import LiteralString
from eth_account import Account
from eth_keys.datatypes import PrivateKey
import os

# Настройки
CHAIN_ID = 1337         # уникальный ID блокчейн-сети
GAS_LIMIT = 0x1C9C380   # 30M - лимит газа на блок

CLIQUE_PERIOD = 2       # секунды между блоками (каждые 2 секунды - новый блок)
CLIQUE_EPOCH = 30000    # количество блоков в эпохе
                        # - при достижении такого размера чистятся логи и т.п.
                        # выполняются контрольные точки, происходит смена состояния

PASSWORD = "devpass123" # пароль для шифрования keystore (ключей аккаунта валидатора)


def generate_accounts():
    """Генерирует 2 валидатора и 1 релейера"""
    validator1 = Account.create()
    validator2 = Account.create()
    relayer = Account.create()

    print(f"Validator 1 address: {validator1.address}")
    print(f"Validator 2 address: {validator2.address}")
    print(f"Relayer     address: {relayer.address}")

    return validator1, validator2, relayer


def build_extra_data(validators):
    """
    Формирует extraData для Clique с несколькими валидаторами.
    Заносится в генезис и хранит список начальных валидаторов.
    Структура: Vanity (32 bytes) + [Signer1 (20 bytes) + Signer2 (20 bytes) + ...] + Seal (65 bytes)
    """
    vanity = "00" * 32
    seal = "00" * 65

    # Сортируем и собираем все адреса валидаторов подряд (без 0x)
    clean = [addr[2:].lower() for addr in validators]
    clean.sort()

    return "0x" + vanity + "".join(clean) + seal


def build_genesis(v1, v2, relayer, extra_data):
    return {
        "config": {
            "chainId": CHAIN_ID,
            "homesteadBlock": 0,
            "eip150Block": 0,
            "eip155Block": 0,
            "eip158Block": 0,
            "byzantiumBlock": 0,
            "constantinopleBlock": 0,
            "petersburgBlock": 0,
            "istanbulBlock": 0,
            "clique": {                     # активация консенсуса PoA
                "period": CLIQUE_PERIOD,
                "epoch": CLIQUE_EPOCH
            }
        },

        "nonce": "0x0",     # nonce - не нужен для PoA
        "timestamp": "0x0", # timestamp - время создания блока (точка отсчёта)

        "extraData": extra_data,    # список начальных валидаторов

        "gasLimit": hex(GAS_LIMIT), # макс. объём газа на блок

        "difficulty": "0x1",        # сложность сети; для PoA не имеет значения

        "mixHash": "0x" + "00" * 32,    # нужен для PoW, а для PoA просто нулями заполняется

        "coinbase": "0x" + "00" * 20,   # адрес майнера получающего награду; в Clique его нет, поэтому 0

        "alloc": {
            # Раздаем баланс всем, чтобы они могли платить газ (если нужно)
            v1.address: {
                "balance": hex(10**18)
            },

            v2.address: {
                "balance": hex(10**18)
            },

            relayer.address: {
                "balance": hex(5 * 10**17)
            }
        },

        "number": "0x0",    # номер блока (0)
        "gasUsed": "0x0",   # объём потраченного газа в этом блоке (0)

        "parentHash": "0x" + "00" * 32  # ссылка на родительский блок (0 для генезиса)
    }


def save_keystore(account, node_data_dir, password):
    """
    Шифрует приватный ключ аккаунта валидатора и 
    сохраняет в формате, который понимает Geth.
    """
    keystore_dir = node_data_dir / "keystore"

    keystore_dir.mkdir(parents=True, exist_ok=True)

    # Шифруем ключ стандартным алгоритмом Ethereum
    encrypted = account.encrypt(password)

    # Имя файла по стандарту Geth: UTC--<время>--<адрес>
    file_name = f"UTC--{account.address[2:].lower()}"

    with open(keystore_dir / file_name, "w") as f:
        json.dump(encrypted, f)


def save_env_file(base_dir, v1_addr, v2_addr):
    env_path = base_dir / ".env"

    # Значения по умолчанию для локальной разработки
    db_user = "dev"
    db_pass = "devpass_secure_123"
    db_name = "unidapp"
    db_host = "127.0.0.1"
    db_port = "5433"

    # Если .env уже существует, пытаемся сохранить текущие настройки БД
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DB_USER="):
                    db_user = line.strip().split("=")[1]

                if line.startswith("DB_PASSWORD="):
                    db_pass = line.strip().split("=")[1]

                if line.startswith("DB_NAME="):
                    db_name = line.strip().split("=")[1]

                if line.startswith("DB_HOST="):
                    db_host = line.strip().split("=")[1]

                if line.startswith("DB_PORT="):
                    db_port = line.strip().split("=")[1]

    content = f"""
# --- Конфигурация Блокчейна ---
VALIDATOR_1_ADDRESS={v1_addr}
VALIDATOR_2_ADDRESS={v2_addr}

# --- Конфигурация Базы Данных ---
DB_USER={db_user}
DB_PASSWORD={db_pass}
DB_NAME={db_name}
DB_HOST={db_host}
DB_PORT={db_port}
"""

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

# IP и tcp порты для подключения к нодам
NODE1_IP = "172.30.0.10"
NODE1_PORT = 30303          # Стандартный порт P2P для Geth
NODE2_IP = "172.30.0.20"
NODE2_PORT = 30304          # Второй порт, чтобы не было конфликта на хосте, если пробрасывать


def node_pubkey_hex(priv: bytes) -> str:
    """Извлекает публичный узла ключ сети (Enode ID) из приватного ключа сети."""
    return PrivateKey(priv).public_key.to_hex()[2:]


def save_nodekey(node_data_dir: Path, priv: bytes) -> str:
    """
    Сохраняет приватный сетевой ключ в файл 'nodekey'.
    И возвращает публичную пару.
    
    Geth при запуске ищет файл <datadir>/geth/nodekey.
    Если файл есть, Geth использует его как постоянный ID ноды.
    Если файла нет, Geth генерирует случайный ключ при каждом старте,
    что ломает статические соединения (static-nodes).
    """
    geth_dir = node_data_dir / "geth"
    geth_dir.mkdir(parents=True, exist_ok=True)
    (geth_dir / "nodekey").write_text(priv.hex())
    return node_pubkey_hex(priv)


def write_geth_config(geth_dir: Path, static_nodes: list[str]) -> None:
    """
    Создает файл config.toml для Geth.

    Находясь в режиме nodiscover, без этого файла, ноды не будут стучаться на какие-либо
    адреса. Но, имея этот файл, нода обратиться по адресам в нём и установится соединение нод.
    """
    lines = ["[Node.P2P]", "StaticNodes = ["]
    for enode in static_nodes:
        # Экранируем кавычки для корректного TOML/JSON формата внутри массива
        lines.append(f'  "{enode}",')
    lines.append("]")
    # Записываем конфиг. Geth читает config.toml из папки datadir или geth
    (geth_dir / "config.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def setup_p2p(base_dir: Path) -> None:
    """
    Основная функция настройки P2P-сети между двумя нодами.
    
    1. Генерирует уникальные сетевые ключи (не путать с ключами кошельков!).
    2. Сохраняет их в nodekey, чтобы ID нод был постоянным.
    3. Формирует Enode URL для каждой ноды.
    4. Создает static-nodes.json, чтобы ноды автоматически соединялись при старте.
    5. Обновляет .env файл переменными для docker-compose (если нужно передавать через флаги).
    """
    
    # 1. Генерация случайных приватных ключей для сетевого уровня (32 байта энтропии)
    # Эти ключи отвечают только за шифрование трафика между нодами и их идентификацию в P2P.
    priv1 = os.urandom(32)
    priv2 = os.urandom(32)

    # 2. Сохранение ключей в файловую систему нод и получение публичных частей
    # После этого шага у нас есть постоянные ID для node1 и node2
    pub1 = save_nodekey(base_dir / "node1_data", priv1)
    pub2 = save_nodekey(base_dir / "node2_data", priv2)

    # 3. Формирование Enode URL
    # Формат: enode://<PubKey>@<IP>:<Port>
    # IP-адреса должны быть доступны изнутри Docker-контейнеров друг для друга.
    enode1 = f"enode://{pub1}@{NODE1_IP}:{NODE1_PORT}"
    enode2 = f"enode://{pub2}@{NODE2_IP}:{NODE2_PORT}"
    # Список всех нод в сети. Каждая нода должна знать этот список целиком.
    static_nodes = [enode1, enode2]

    # 4. Создание global static-nodes.json в корне infra (для справки или ручного копирования)
    with open(base_dir / "static-nodes.json", "w", encoding="utf-8") as f:
        json.dump(static_nodes, f, indent=2)

    # 5. Запись конфигурации в папки конкретных нод
    # Geth будет читать эти файлы при запуске и пытаться подключиться к указанным пирам
    write_geth_config(base_dir / "node1_data" / "geth", static_nodes)
    write_geth_config(base_dir / "node2_data" / "geth", static_nodes)

    # 6. Обновление файла .env
    # Мы сохраняем список bootnodes/static nodes в переменную окружения, 
    # чтобы можно было передать её в docker-compose, если не используются файлы конфигов.
    bootnodes = ",".join(static_nodes)
    env_path = base_dir / ".env"
    env_lines: list[str] = []
    
    # Читаем существующий .env, если он есть, чтобы не затереть другие переменные (DB_USER и т.д.)
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()
    
    # Удаляем старые версии переменных P2P, если они были
    env_lines = [
        l for l in env_lines
        if not l.startswith(("BOOTNODES=", "BOOTNODE_KEY=", "BOOTNODE_PUB=", "BOOTNODE_ENODE="))
    ]
    # Добавляем новую строку с актуальными_enode_
    env_lines.append(f"BOOTNODES={bootnodes}")
    # Перезаписываем файл
    env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    print("P2P config created")
    print("node1 enode:", enode1)
    print("node2 enode:", enode2)


def main():
    """
    Точка входа. Выполняет полную генерацию артефактов для запуска сети.
    """
    base_dir = Path(__file__).parent.parent

    # --- ЧАСТЬ 1: Блокчейн-уровень (Аккаунты и Genesis) ---
    
    # Генерируем 2 валидатора (подписанты блоков) и 1 релейера (пользователь)
    v1, v2, relayer = generate_accounts()

    # Формируем поле extraData для genesis-блока.
    # В Clique это поле содержит список адресов валидаторов, имеющих право майнить.
    extra_data: LiteralString = build_extra_data([
        v1.address,
        v2.address
    ])

    # Создаем структуру genesis.json
    genesis = build_genesis(
        v1,
        v2,
        relayer,
        extra_data
    )

    # Сохраняем genesis.json в корень infra
    with open(base_dir / "genesis.json", "w") as f:
        json.dump(genesis, f, indent=2)

    # Сохраняем пароль для разблокировки аккаунтов в Geth
    with open(base_dir / "password.txt", "w") as f:
        f.write(PASSWORD + "\n")

    # --- ЧАСТЬ 2: Keystore (Хранение ключей аккаунтов) ---
    
    # Шифруем приватные ключи валидаторов и кладем в папки данных нод.
    # Node1 получит ключ Валидатора 1, Node2 — ключ Валидатора 2.
    save_keystore(
        v1,
        base_dir / "node1_data",
        PASSWORD
    )

    save_keystore(
        v2,
        base_dir / "node2_data",
        PASSWORD
    )

    # Сохраняем открытые приватные ключи в JSON (ТОЛЬКО ДЛЯ РАЗРАБОТКИ! Не коммитить в Git!)
    keys = {
        "validator_1": {
            "address": v1.address,
            "private_key": v1.key.hex()
        },

        "validator_2": {
            "address": v2.address,
            "private_key": v2.key.hex()
        },

        "relayer": {
            "address": relayer.address,
            "private_key": relayer.key.hex()
        },

        "chain_id": CHAIN_ID
    }

    scripts_dir = base_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    with open(scripts_dir / "generated_keys.json", "w") as f:
        json.dump(keys, f, indent=2)

    # Сохраняем адреса валидаторов в .env для docker-compose (флаги --unlock и --miner.etherbase)
    save_env_file(
        base_dir,
        v1.address,
        v2.address
    )

    # --- ЧАСТЬ 3: Сетевой уровень (P2P) ---
    
    # Настраиваем сетевые ключи и статические пиры, чтобы ноды увидели друг друга
    setup_p2p(base_dir)

    print("\nSUCCESS")
    print("genesis.json created")
    print(".env created")
    print("keystore files created")
    print("static-nodes.json created")


if __name__ == "__main__":
    main()
