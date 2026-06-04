.PHONY: up down reset logs migrate build pull-images prod-up prod-down prod-logs

ENV_FILE := infra/.env
COMPOSE := docker compose --env-file $(ENV_FILE)
COMPOSE_PROD := docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file $(ENV_FILE)

# Предзагрузка образов с Docker Hub (повторы при TLS timeout)
pull-images:
	chmod +x scripts/pull-base-images.sh
	./scripts/pull-base-images.sh

# Единый запуск всего проекта в Docker (setup → pull → build → migrate → up)
up:
	chmod +x scripts/docker-up.sh scripts/pull-base-images.sh
	./scripts/docker-up.sh

down:
	$(COMPOSE) down

# Полный сброс: контейнеры, тома БД, данные нод и genesis (повторная генерация ключей)
reset:
	$(COMPOSE) down -v --remove-orphans 2>/dev/null || true
	rm -rf infra/node1_data infra/node2_data infra/genesis.json infra/password.txt \
		infra/static-nodes.json infra/scripts/generated_keys.json infra/.env
	rm -f smartcontracts/deployed.json
	@echo "Сброшено. Запустите: make up"

logs:
	$(COMPOSE) logs -f

# Сборка образов + миграции БД
build:
	@test -f $(ENV_FILE) || (echo "Нет $(ENV_FILE). Сначала: make up (шаг setup)" && exit 1)
	$(COMPOSE) build
	./scripts/migrate.sh

# Только миграции (образ backend должен быть собран, db — доступна)
migrate:
	./scripts/migrate.sh

# Production deploy on server (see README «Развёртывание на сервере»)
prod-up:
	chmod +x scripts/deploy-server.sh scripts/pull-base-images.sh
	./scripts/deploy-server.sh

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f
