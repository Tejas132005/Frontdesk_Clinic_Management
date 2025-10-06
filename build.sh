#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Setting up initial data..."
python manage.py setup_initial_data --noinput || echo "Initial data setup completed or already exists"

echo "Build completed successfully!"