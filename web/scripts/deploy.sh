#!/usr/bin/env bash
# ============================================================
# RCCM — Procédure de déploiement Linux / macOS
# À exécuter depuis le dossier : web/
# Usage : bash scripts/deploy.sh [--no-static]
# ============================================================
set -euo pipefail

BACKEND_DIR="$(dirname "$0")/../backend_django"
SKIP_STATIC=0
[[ "${1:-}" == "--no-static" ]] && SKIP_STATIC=1

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[AVERT]${NC} $*"; }
fail() { echo -e "${RED}[ECHEC]${NC} $*"; exit 1; }

echo ""
echo "==================================================="
echo "  RCCM — Déploiement  |  $(date '+%Y-%m-%d %H:%M:%S')"
echo "==================================================="
echo ""

[[ -f "$BACKEND_DIR/manage.py" ]] || fail "manage.py introuvable dans $BACKEND_DIR"
cd "$BACKEND_DIR"

# ── Étape 1 : Contrôle pré-déploiement ──────────────────────
echo "[1/5] Contrôle pré-déploiement …"
if ! python manage.py check_deploy; then
    warn "Des problèmes ont été détectés. Continuer ? (o/N)"
    read -r CONT
    [[ "${CONT,,}" == "o" ]] || { echo "Déploiement annulé."; exit 1; }
fi

# ── Étape 2 : Migrations ─────────────────────────────────────
echo ""
echo "[2/5] Application des migrations …"
python manage.py migrate --no-input || fail "Les migrations ont échoué."
ok "Migrations appliquées."

# ── Étape 3 : Vérification post-migration ───────────────────
echo ""
echo "[3/5] Vérification schéma post-migration …"
python manage.py check_deploy || fail "Schéma toujours incohérent après migration."
ok "Schéma cohérent."

# ── Étape 4 : Collectstatic ──────────────────────────────────
if [[ "$SKIP_STATIC" -eq 0 ]]; then
    echo ""
    echo "[4/5] Collecte des fichiers statiques …"
    python manage.py collectstatic --no-input --clear \
        && ok "Fichiers statiques collectés." \
        || warn "collectstatic a échoué — non bloquant."
else
    echo "[4/5] collectstatic ignoré (--no-static)."
fi

# ── Étape 5 : Rapport ────────────────────────────────────────
echo ""
echo "==================================================="
ok "RCCM prêt — démarrez le serveur :"
echo "     python manage.py runserver"
echo "==================================================="
echo ""
