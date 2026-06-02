#!/bin/sh
# Инициализация datadir только если chaindata ещё нет (повторный compose up).
set -eu
DATADIR="${1:?datadir}"
GENESIS="${2:?genesis}"

if [ -f "$DATADIR/geth/chaindata/CURRENT" ]; then
  echo "Geth already initialized in $DATADIR, skipping init."
  exit 0
fi

echo "Initializing geth in $DATADIR ..."
exec geth --datadir "$DATADIR" init "$GENESIS"
