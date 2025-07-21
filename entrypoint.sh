#!/bin/sh
set -e

# 1) Run migrations
python manage.py migrate --noinput

# 2) Create superuser if not exists
python - <<'EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'saida')
email    = os.getenv('DJANGO_SUPERUSER_EMAIL',    'saidaangenakeu@gmail.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'Qwerty@123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
EOF

# 3) Collect static files
python manage.py collectstatic --noinput

# 4) Start Gunicorn
exec gunicorn mission_manager.wsgi:application --bind 0.0.0.0:8000