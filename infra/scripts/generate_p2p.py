#!/usr/bin/env python3
"""
Скрипт для генерации сетевых ключей (nodekey) и настройки статических пиров (static-nodes).
Этот скрипт НЕ трогает аккаунты валидаторов (keystore), он отвечает только за то,
как контейнеры Docker находят друг друга в сети (P2P уровень).

Запускать, если нужно пересоздать сетевое соединение или если ноды не видят друг друга.
!!!Этот скрипт ВКЛЮЧЁН в скрипт setup.py!!!
"""

import json
import os
from pathlib import Path

# Библиотека eth-keys нужна для криптографических операций с ключами devp2p
from eth_keys.datatypes import PrivateKey

# --- НАСТРОЙКИ СЕТИ DOCKER ---
# IP-адреса должны совпадать с теми, что прописаны в docker-compose.yml в разделе networks.
# Если вы не задавали статические IP вручную, Docker выдаст их автоматически, 
# и тогда эти константы нужно будет обновить или использовать имена сервисов вместо IP.
NODE1_IP = "172.30.0.10"
NODE1_PORT = 30303  # Стандартный порт для P2P общения Geth

NODE2_IP = "172.30.0.20"
NODE2_PORT = 30304  # Второй порт (важно, чтобы не было конфликта, если пробрасывать на хост)


def node_pubkey_hex(priv: bytes) -> str:
    """
    Вычисляет публичный ключ сети (Enode ID) из приватного ключа.
    
    В протоколе devp2p узел идентифицируется своим публичным ключом.
    Этот ID используется в адресе enode://<ID>@IP:PORT.
    
    Args:
        priv: 32 байта приватного ключа.
    Returns:
        Hex-строка публичного ключа без префикса '0x'.
    """
    # Создаем объект ключа и получаем публичную часть
    # [2:] убирает префикс '0x', так как в enode URL он не нужен
    return PrivateKey(priv).public_key.to_hex()[2:]


def save_nodekey(node_data_dir: Path, priv: bytes) -> str:
    """
    Сохраняет приватный сетевой ключ в файл 'nodekey' внутри папки данных ноды.
    
    Зачем это нужно?
    По умолчанию Geth генерирует случайный сетевой ключ при каждом запуске.
    Это меняет Enode URL ноды. Если Enode меняется, другие ноды не могут 
    подключиться к ней по старому адресу из static-nodes.json.
    Сохраняя ключ в файл, мы фиксируем ID ноды навсегда.
    
    Args:
        node_data_dir: Путь к папке данных (например, ./node1_data).
        priv: Сгенерированный приватный ключ.
    Returns:
        Публичный ключ (для формирования enode URL).
    """
    geth_dir = node_data_dir / "geth"
    # Создаем папку geth, если её нет (там хранятся ключи и конфиги)
    geth_dir.mkdir(parents=True, exist_ok=True)
    
    # Записываем приватный ключ в файл. Geth читает его при старте.
    (geth_dir / "nodekey").write_text(priv.hex())
    
    return node_pubkey_hex(priv)


def write_geth_config(geth_dir: Path, static_nodes: list[str]) -> None:
    """
    Создает файл config.toml с указанием статических пиров.
    
    Geth поддерживает два способа задания постоянных пиров:
    1. Файл static-nodes.json (старый формат).
    2. Секция [Node.P2P] в config.toml (новый, более надежный формат).
    
    Мы используем TOML, чтобы явно указать ноде: "Подключайся к этим адресам".
    
    Args:
        geth_dir: Путь к папке <datadir>/geth.
        static_nodes: Список полных enode-адресов всех нод в сети.
    """
    lines = ["[Node.P2P]", "StaticNodes = ["]
    for enode in static_nodes:
        # Добавляем каждый адрес в массив
        lines.append(f'  "{enode}",')
    lines.append("]")
    
    # Записываем конфиг. Geth подхватит его при следующем старте.
    (geth_dir / "config.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """
    Основная логика настройки P2P.
    1. Генерирует новые сетевые ключи.
    2. Фиксирует их в файлах нод.
    3. Обновляет конфигурацию соединений.
    """
    base_dir = Path(__file__).parent.parent

    print("🔄 Генерация новых P2P ключей...")
    
    # 1. Генерируем случайные приватные ключи для сетевого уровня (32 байта)
    # Это НЕ ключи от кошельков (validator keys), это ключи для "сетевой карты" ноды.
    priv1 = os.urandom(32)
    priv2 = os.urandom(32)

    # 2. Сохраняем ключи в папки данных нод и получаем их публичные ID
    pub1 = save_nodekey(base_dir / "node1_data", priv1)
    pub2 = save_nodekey(base_dir / "node2_data", priv2)

    # 3. Формируем полные адреса Enode
    # Формат: enode://<PubKey>@<IP>:<Port>
    # Эти адреса говорят ноде: "Ищи соседа по этому IP и порту, вот его паспорт (PubKey)"
    static_nodes = [
        f"enode://{pub1}@{NODE1_IP}:{NODE1_PORT}",
        f"enode://{pub2}@{NODE2_IP}:{NODE2_PORT}",
    ]

    # 4. Сохраняем общий список нод в корень проекта (для удобства/бэкапа)
    with open(base_dir / "static-nodes.json", "w", encoding="utf-8") as f:
        json.dump(static_nodes, f, indent=2)

    # 5. Прописываем этот список в конфиги каждой ноды
    # Теперь node1 знает про node2, а node2 про node1
    write_geth_config(base_dir / "node1_data" / "geth", static_nodes)
    write_geth_config(base_dir / "node2_data" / "geth", static_nodes)

    # 6. Обновляем переменную BOOTNODES в файле .env
    # Это нужно, если вы передаете список нод через аргументы командной строки в docker-compose
    bootnodes = ",".join(static_nodes)
    
    env_path = base_dir / ".env"
    env_lines: list[str] = []
    
    # Читаем текущий .env, чтобы не затереть другие настройки (DB_USER, PASSWORD и т.д.)
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()
    
    # Удаляем старую строку BOOTNODES, если она была
    env_lines = [l for l in env_lines if not l.startswith("BOOTNODES=")]
    
    # Добавляем новую актуальную строку
    env_lines.append(f"BOOTNODES={bootnodes}")
    
    # Перезаписываем файл
    env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    print("P2P config created (config.toml + BOOTNODES in .env)")
    print(f"   Node1 PubKey: {pub1[:10]}...")
    print(f"   Node2 PubKey: {pub2[:10]}...")
    print("   Не забудьте перезапустить контейнеры: docker compose down && docker compose up -d")


if __name__ == "__main__":
    main()