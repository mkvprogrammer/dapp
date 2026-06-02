FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl jq \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY smartcontracts/package.json smartcontracts/package-lock.json* ./
RUN npm ci

COPY smartcontracts/ .
RUN node scripts/compile-offline.js
COPY docker/contracts/deploy.sh /deploy.sh
RUN chmod +x /deploy.sh

ENTRYPOINT ["/deploy.sh"]
