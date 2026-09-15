#!/bin/bash
set -euo pipefail

docker compose up -d --build
docker compose ps
