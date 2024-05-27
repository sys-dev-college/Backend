#!/bin/sh

until cd /app

do
    echo "Waiting for server volume..."
done
alembic upgrade head

hypercorn main:app --bind 0.0.0.0:8000
