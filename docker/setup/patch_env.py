#!/usr/bin/env python3
"""Перезаписывает host-специфичные переменные в infra/.env для docker-compose."""

from __future__ import annotations

import sys
from pathlib import Path

DOCKER_OVERRIDES = {
    "DB_HOST": "db",
    "DB_PORT": "5432",
    'BLOCKCHAIN_URL': '"http://node1:8545"',
}


def patch_env(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f".env not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    keys_done = set()
    out: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in DOCKER_OVERRIDES:
            out.append(f"{key}={DOCKER_OVERRIDES[key]}")
            keys_done.add(key)
        else:
            out.append(line)

    for key, value in DOCKER_OVERRIDES.items():
        if key not in keys_done:
            out.append(f"{key}={value}")

    path.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    patch_env(Path(sys.argv[1]))
