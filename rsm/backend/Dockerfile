# Image de test RSM — backend Django
# ⚠️ Image destinée à l'environnement de TEST FONCTIONNEL.
# Non optimisée pour la production.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système : PostgreSQL client + locales FR/AR
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        locales \
        gettext \
    && sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
    && sed -i -e 's/# ar_MR UTF-8/ar_MR UTF-8/' /etc/locale.gen \
    && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copie du code (en développement, montage volumique recommandé)
COPY . .

EXPOSE 8000
