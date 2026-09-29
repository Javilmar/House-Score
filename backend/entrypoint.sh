#!/bin/sh
set -e
# Migraciones automáticas al arrancar la API (SC-003)
alembic upgrade head
exec "$@"
