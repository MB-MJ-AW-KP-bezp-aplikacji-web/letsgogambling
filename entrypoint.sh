#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate

echo "Starting Daphne web server..."
daphne -b 0.0.0.0 -p 8000 casino.asgi:application &
DAPHNE_PID=$!

echo "Starting roulette game worker..."
python manage.py run_roulette_game &
ROULETTE_PID=$!

echo "Both processes started. PIDs: Daphne=$DAPHNE_PID, Roulette=$ROULETTE_PID"

# Trap SIGTERM and SIGINT to gracefully shutdown both processes
trap "echo 'Shutting down...'; kill $DAPHNE_PID $ROULETTE_PID; wait $DAPHNE_PID $ROULETTE_PID; exit 0" TERM INT

# Wait for both background processes
wait
