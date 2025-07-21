#!/bin/sh
set -e

# Appliquer migrations
python manage.py migrate --noinput

# Créer automatiquement le super-utilisateur si besoin
python manage.py shell -c "\
from django.contrib.auth import get_user_model; \
User = get_user_model(); \
\
username = '${DJANGO_SUPERUSER_USERNAME:-admin}'; \
email = '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}'; \
password = '${DJANGO_SUPERUSER_PASSWORD:-adminpass}'; \
\
if not User.objects.filter(username=username).exists(): \
    User.objects.create_superuser(username, email, password);\
"

# Collectstatic (si pas déjà fait)
python manage.py collectstatic --noinput

# Lancer Gunicorn
exec gunicorn mission_manager.wsgi:application --bind 0.0.0.0:8000