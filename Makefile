.PHONY: up down reset logs

# Единый запуск всего проекта в Docker
up:
	./scripts/docker-up.sh

down:
	docker compose --env-file infra/.env down

# Полный сброс: контейнеры, тома БД, данные нод и genesis (повторная генерация ключей)
reset:
	docker compose --env-file infra/.env down -v --remove-orphans 2>/dev/null || true
	rm -rf infra/node1_data infra/node2_data infra/genesis.json infra/password.txt \
		infra/static-nodes.json infra/scripts/generated_keys.json infra/.env
	rm -f smartcontracts/deployed.json
	@echo "Сброшено. Запустите: make up"

logs:
	docker compose --env-file infra/.env logs -f
