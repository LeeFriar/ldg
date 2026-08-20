#!/bin/sh
set -eu

# Support both the Docker Compose v2 plugin and legacy docker-compose.
if docker compose version >/dev/null 2>&1; then
  exec docker compose -f compose.yaml "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose -f compose.yaml "$@"
fi

echo "Docker Compose is not installed on this Jenkins worker." >&2
exit 127
