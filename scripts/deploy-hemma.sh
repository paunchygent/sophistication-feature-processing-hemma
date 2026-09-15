#!/bin/bash
set -euo pipefail

docker volume inspect gothenburg-lexicon-config >/dev/null 2>&1 || \
  docker volume create gothenburg-lexicon-config >/dev/null
docker volume inspect gothenburg-lexicon-workspace >/dev/null 2>&1 || \
  docker volume create gothenburg-lexicon-workspace >/dev/null

docker compose up -d --build
docker compose ps
