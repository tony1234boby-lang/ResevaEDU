#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Initialize database config and roles
python reserva/scratch/setup_google_oauth.py
python reserva/scratch/setup_roles_and_test_users.py
