#!/bin/bash
set -euo pipefail

RPC_URL="${BLOCKCHAIN_RPC_URL:-http://node1:8545}"
KEYS_FILE="${KEYS_FILE:-/keys/generated_keys.json}"
FORCE="${FORCE_REDEPLOY:-0}"
OUT_DIR="${OUT_DIR:-/out}"

echo "==> Waiting for blockchain RPC at ${RPC_URL} ..."
for i in $(seq 1 90); do
  if curl -sf -X POST "$RPC_URL" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    | grep -q '"result"'; then
    echo "RPC is up."
    break
  fi
  sleep 2
  if [ "$i" -eq 90 ]; then
    echo "RPC timeout" >&2
    exit 1
  fi
done

if [ ! -f "$KEYS_FILE" ]; then
  echo "Keys file not found: $KEYS_FILE (run setup first)" >&2
  exit 1
fi

hex_key() {
  local k
  k=$(jq -r "$1" "$KEYS_FILE")
  case "$k" in
    0x*) echo "$k" ;;
    *) echo "0x$k" ;;
  esac
}

DEPLOYER=$(hex_key '.validator_1.private_key')
ORGANIZER=$(hex_key '.validator_2.private_key')
RELAYER=$(hex_key '.relayer.private_key')

cat > /app/.env <<EOF
LOCAL_POA_DEPLOYER_KEY=${DEPLOYER}
LOCAL_POA_ORGANIZER_KEY=${ORGANIZER}
LOCAL_POA_RELAYER_KEY=${RELAYER}
BLOCKCHAIN_RPC_URL=${RPC_URL}
EOF

echo "==> Wrote /app/.env from generated_keys.json"

if [ "$FORCE" != "1" ] && { [ -f "$OUT_DIR/deployed.json" ] || [ -f /app/deployed.json ]; }; then
  echo "==> deployed.json already present, syncing to host (FORCE_REDEPLOY=1 to redeploy)..."
  mkdir -p "$OUT_DIR"
  SRC="${OUT_DIR}/deployed.json"
  [ -f /app/deployed.json ] && SRC="/app/deployed.json"
  cp -f "$SRC" "$OUT_DIR/deployed.json"
  [ -d /app/artifacts ] && cp -a /app/artifacts "$OUT_DIR/" 2>/dev/null || true
  exit 0
fi

if [ ! -d /app/artifacts/contracts ]; then
  if [ -d "$OUT_DIR/artifacts/contracts" ]; then
    echo "==> Using precompiled artifacts from ${OUT_DIR} ..."
    cp -a "$OUT_DIR/artifacts" /app/
  else
    echo "==> Artifacts missing, offline compile (solc npm) ..."
    node scripts/compile-offline.js
  fi
fi

echo "==> hardhat deploy ..."
export BLOCKCHAIN_RPC_URL
npx hardhat run scripts/deploy.js --network dockerPoA --no-compile

echo "==> Syncing deployed.json and artifacts to ${OUT_DIR} ..."
mkdir -p "$OUT_DIR"
cp -f /app/deployed.json "$OUT_DIR/deployed.json"
cp -a /app/artifacts "$OUT_DIR/"

echo "==> Contracts deployed."
