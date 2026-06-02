#!/bin/sh
set -eu

cd /infra

if [ ! -f genesis.json ]; then
  echo "==> Generating genesis, validators, P2P config..."
  python scripts/setup.py
else
  echo "==> genesis.json exists, skipping key generation."
fi

echo "==> Patching infra/.env for Docker network..."
python /patch_env.py /infra/.env

echo "==> Setup complete."
