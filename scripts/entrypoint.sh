#!/bin/sh

if [ "$DATABASE" = "odoo" ]; then
    echo "Waiting for postgres..."

    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py makemigrations users
python manage.py migrate

exec "$@"
