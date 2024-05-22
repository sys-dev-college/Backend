#!/bin/sh

until cd /app

do
    echo "Waiting for server volume..."
done

hypercorn main:app --bind 0.0.0.0:8000
