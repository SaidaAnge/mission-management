FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# 1. Installer les dépendances
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 2. Copier le code
COPY . /app/

# 3. Préparer les statiques
RUN mkdir -p /app/staticfiles \
    && python manage.py collectstatic --noinput \
    && python manage.py migrate --noinput

EXPOSE 8000

CMD ["gunicorn", "mission_manager.wsgi:application", "--bind", "0.0.0.0:8000"]
