# 1. Image de base Python
FROM python:3.10-slim

# 2. Variables d’environnement Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Installation des dépendances système requises par mysqlclient
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
        libssl-dev \
        && rm -rf /var/lib/apt/lists/*

# 4. Création du répertoire de l’application
WORKDIR /app

# 5. Copier et installer les dépendances Python
COPY requirement.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirement.txt

# 6. Copier le code source
COPY . /app/

# 8. Exposer le port de l’application
EXPOSE 8000

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Remplace la ligne CMD par :
ENTRYPOINT ["/app/entrypoint.sh"]