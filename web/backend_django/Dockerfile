FROM python:3.11-slim

# ── Dépendances système ──────────────────────────────────────────────────────
# libpq-dev + gcc   : compilation psycopg2
# fonts-dejavu-core : polices Unicode Latin/Cyrillique (DejaVuSans) pour ReportLab
# fonts-noto-core   : polices Noto (arabe, latin, ...) pour le rendu arabe ReportLab
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dépendances Python ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Code source ──────────────────────────────────────────────────────────────
COPY . .

# ── Répertoires d'exécution ──────────────────────────────────────────────────
# media/       : fichiers uploadés (pièces jointes, documents)
# staticfiles/ : fichiers statiques collectés (whitenoise)
# logs/        : journaux Django (RotatingFileHandler — doit exister au démarrage)
RUN mkdir -p /app/media /app/staticfiles /app/logs

# ── Sécurité : utilisateur non-root ─────────────────────────────────────────
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# ── Démarrage (remplacé par le command: du docker-compose en production) ──────
# En standalone (docker run), gunicorn démarre directement.
# En docker-compose, le command: exécute migrate + collectstatic avant ce CMD.
CMD ["gunicorn", "registre_rc.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
