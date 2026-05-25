# Данный файл запускать НЕ НУЖНО

import os
from pathlib import Path
from eth_account import Account

def main():
    print("🎲 Генерирую новые Web3 аккаунты...\n")

    # Включаем экспериментальную поддержку функций eth_account (требуется для create)
    Account.enable_unaudited_hdwallet_features()

    # Генерируем 3 случайных кошелька
    deployer = Account.create()
    organizer = Account.create()
    relayer = Account.create()

    # Выводим публичные адреса в консоль для наглядности
    print("ℹ️  Сгенерированные адреса (публичные):")
    print(f"Deployer (Admin):   {deployer.address}")
    print(f"Organizer (Teacher): {organizer.address}")
    print(f"Relayer (User):      {relayer.address}\n")

    # Формируем текстовое содержимое для файла .env
    env_content = (
        f"# Приватные ключи для сети localPoA\n"
        f'LOCAL_POA_DEPLOYER_KEY=0x{deployer.key.hex()}\n'
        f'LOCAL_POA_ORGANIZER_KEY=0x{organizer.key.hex()}\n'
        f'LOCAL_POA_RELAYER_KEY=0x{relayer.key.hex()}\n'
    )

    # Определяем путь к файлу .env в корне папки смарт-контрактов
    # Скрипт подниметься на один уровень выше текущей папки и создаст/перезапишет .env
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"

    # Записываем данные в файл
    with open(env_path, "w", encoding="utf-8") as env_file:
        env_file.write(env_content)
        
    print(f"📄 Приватные ключи успешно сохранены в: {env_path}")

    # Выводим готовую подсказку для конфигурации Hardhat
    print("\n🛠️  Скопируйте этот блок в ваш hardhat.config.js в секцию accounts:")
    print("accounts: [")
    print("    process.env.LOCAL_POA_DEPLOYER_KEY,")
    print("    process.env.LOCAL_POA_ORGANIZER_KEY,")
    print("    process.env.LOCAL_POA_RELAYER_KEY")
    print("]")

if __name__ == "__main__":
    main()
