#!/bin/bash
# setup.sh — configuración inicial del proyecto
# Genera el archivo .env con los valores que elijas.
# Uso: bash setup.sh

set -e
set -a  # auto-exportar todas las variables para que Python las vea via os.environ

# ── Utilidades ─────────────────────────────────────────────────────────────────
gen_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe($1))"
}

gen_hex() {
    python3 -c "import secrets; print(secrets.token_hex($1))"
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Setup: Django Skeleton"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Verificar .env existente ──────────────────────────────────────────────────
if [ -f .env ]; then
    echo "Ya existe un archivo .env con la siguiente configuración:"
    echo ""
    grep -v '^#' .env | grep -v '^$' | head -10
    echo "..."
    echo ""
    read -p "¿Sobreescribir el .env existente? (s/N): " OVERWRITE
    if [ "${OVERWRITE}" != "s" ] && [ "${OVERWRITE}" != "S" ]; then
        echo "Cancelado. El archivo .env no fue modificado."
        exit 0
    fi
    echo ""
fi

# ── Entorno ──────────────────────────────────────────────────────────────────
read -p "¿Entorno? (dev/prod) [prod]: " ENV_TYPE
ENV_TYPE=${ENV_TYPE:-prod}
if [ "${ENV_TYPE}" = "dev" ]; then
    DEBUG=True
else
    DEBUG=False
fi
echo ""

# ── Nombre del proyecto ───────────────────────────────────────────────────────
DIR_NAME=$(basename "$(pwd)")
read -p "Nombre del proyecto [${DIR_NAME}]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-${DIR_NAME}}
# Solo letras, números y guiones
PROJECT_NAME=$(echo "${PROJECT_NAME}" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
echo ""

# ── Dominio de Django ─────────────────────────────────────────────────────────
while true; do
    read -p "Dominio para Django (ej: miapp.com): " DOMAIN
    [ -n "${DOMAIN}" ] && break
    echo "  El dominio no puede estar vacío."
done
echo ""

# ── PostgreSQL ────────────────────────────────────────────────────────────────
echo "PostgreSQL:"
echo "  1) Contenedor Docker — recomendado, PostgreSQL incluido en docker-compose"
echo "  2) Host del servidor — PostgreSQL ya instalado en el VPS"
echo ""
read -p "Opción [1]: " PG_CHOICE
PG_CHOICE=${PG_CHOICE:-1}
echo ""

if [ "${PG_CHOICE}" = "2" ]; then
    POSTGRES_MODE=host
    POSTGRES_HOST=host.docker.internal
    read -p "  Base de datos PostgreSQL: " POSTGRES_DB
    POSTGRES_DB=${POSTGRES_DB:-${PROJECT_NAME}_db}
    read -p "  Usuario PostgreSQL: " POSTGRES_USER
    POSTGRES_USER=${POSTGRES_USER:-${PROJECT_NAME}_user}
    read -sp "  Contraseña PostgreSQL: " POSTGRES_PASSWORD; echo
    read -p "  Puerto PostgreSQL [5432]: " POSTGRES_PORT
    POSTGRES_PORT=${POSTGRES_PORT:-5432}
    POSTGRES_HOST_PORT=${POSTGRES_PORT}
    echo ""
    echo "  NOTA: Asegúrate de que PostgreSQL esté configurado para aceptar"
    echo "  conexiones desde la red Docker (172.17.0.0/16) en pg_hba.conf"
    echo "  y que listen_addresses incluya la IP del bridge Docker."
    echo ""
else
    POSTGRES_MODE=container
    POSTGRES_HOST=localhost  # Django corre en el host; Docker expone postgres en localhost:5432
    POSTGRES_DB="${PROJECT_NAME}_db"
    POSTGRES_USER="${PROJECT_NAME}_user"
    POSTGRES_PASSWORD=$(gen_secret 24)
    POSTGRES_PORT=5432
    POSTGRES_HOST_PORT=5432
fi

# ── Puertos ───────────────────────────────────────────────────────────────────
read -p "Puerto base de la app Django [8000]: " APP_PORT
APP_PORT=${APP_PORT:-8000}
N8N_PORT=$((APP_PORT + 1))
N8N_MCP_PORT=$((APP_PORT + 2))
echo ""

# ── n8n ───────────────────────────────────────────────────────────────────────
read -p "¿Habilitar n8n? (s/N): " ENABLE_N8N
ENABLE_N8N=${ENABLE_N8N:-N}
echo ""

N8N_DOMAIN=""
N8N_ENCRYPTION_KEY=""
N8N_MCP_ENABLED=""
N8N_API_KEY=""
N8N_MCP_AUTH_TOKEN=""

if [ "${ENABLE_N8N}" = "s" ] || [ "${ENABLE_N8N}" = "S" ]; then
    while true; do
        read -p "  Dominio para n8n (ej: n8n.miapp.com): " N8N_DOMAIN
        [ -n "${N8N_DOMAIN}" ] && break
        echo "  El dominio de n8n no puede estar vacío."
    done
    N8N_ENCRYPTION_KEY=$(gen_secret 32)
    echo "  N8N_ENCRYPTION_KEY generada automáticamente."
    echo ""

    read -p "  ¿Habilitar n8n-MCP? (s/N): " ENABLE_MCP
    ENABLE_MCP=${ENABLE_MCP:-N}
    echo ""

    if [ "${ENABLE_MCP}" = "s" ] || [ "${ENABLE_MCP}" = "S" ]; then
        N8N_MCP_ENABLED=true
        N8N_MCP_AUTH_TOKEN=$(gen_secret 32)
        echo "  N8N_MCP_AUTH_TOKEN generada automáticamente."
        echo "  Recuerda completar N8N_API_KEY en .env después de configurar n8n."
        echo ""
    fi
fi

# ── Admin URL ─────────────────────────────────────────────────────────────────
RANDOM_ADMIN="$(gen_hex 6)/"
read -p "URL del panel admin [${RANDOM_ADMIN}]: " ADMIN_URL
ADMIN_URL=${ADMIN_URL:-${RANDOM_ADMIN}}
echo ""

# ── Email SMTP ────────────────────────────────────────────────────────────────
read -p "¿Configurar email SMTP? (s/N): " ENABLE_EMAIL
ENABLE_EMAIL=${ENABLE_EMAIL:-N}
echo ""

EMAIL_HOST=""
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=""
EMAIL_HOST_PASSWORD=""
DEFAULT_FROM_EMAIL="noreply@${DOMAIN}"

if [ "${ENABLE_EMAIL}" = "s" ] || [ "${ENABLE_EMAIL}" = "S" ]; then
    read -p "  SMTP Host (ej: smtp.gmail.com): " EMAIL_HOST
    read -p "  Puerto [587]: " EMAIL_PORT
    EMAIL_PORT=${EMAIL_PORT:-587}
    read -p "  Usuario: " EMAIL_HOST_USER
    read -sp "  Contraseña: " EMAIL_HOST_PASSWORD; echo
    read -p "  From email [noreply@${DOMAIN}]: " DEFAULT_FROM_EMAIL
    DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL:-noreply@${DOMAIN}}
    echo ""
fi

# ── Generar secretos ──────────────────────────────────────────────────────────
SECRET_KEY=$(gen_secret 50)

# ── Construir ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS ───────────────────────────
ALLOWED_HOSTS="${DOMAIN}"
CSRF_TRUSTED_ORIGINS="https://${DOMAIN}"

# ── Escribir .env (via Python para escapar correctamente caracteres especiales) ──
python3 - << 'PYEOF'
import os

def kv(key, value):
    """Escapa el valor si contiene caracteres especiales del shell."""
    if value and any(c in value for c in '$`"\\'):
        # Usar comillas simples; escapar comillas simples dentro del valor
        value = "'" + value.replace("'", "'\\''") + "'"
    return f"{key}={value}"

lines = [
    "# Generado por setup.sh",
    "# Edita este archivo para ajustar la configuración.",
    "",
    "# ── Proyecto ──────────────────────────────────────────────────────────────",
    kv("PROJECT_NAME", os.environ.get("PROJECT_NAME", "")),
    "",
    "# ── Dominios ──────────────────────────────────────────────────────────────",
    kv("DOMAIN", os.environ.get("DOMAIN", "")),
    "",
    "# ── Puertos ───────────────────────────────────────────────────────────────",
    kv("APP_PORT", os.environ.get("APP_PORT", "8000")),
    kv("N8N_PORT", os.environ.get("N8N_PORT", "8001")),
    kv("N8N_MCP_PORT", os.environ.get("N8N_MCP_PORT", "8002")),
    "",
    "# ── Django ────────────────────────────────────────────────────────────────",
    kv("SECRET_KEY", os.environ.get("SECRET_KEY", "")),
    kv("DEBUG", os.environ.get("DEBUG", "False")),
    kv("ALLOWED_HOSTS", os.environ.get("ALLOWED_HOSTS", "")),
    kv("CSRF_TRUSTED_ORIGINS", os.environ.get("CSRF_TRUSTED_ORIGINS", "")),
    kv("ADMIN_URL", os.environ.get("ADMIN_URL", "admin/")),
    "",
    "# ── PostgreSQL ────────────────────────────────────────────────────────────",
    kv("POSTGRES_MODE", os.environ.get("POSTGRES_MODE", "container")),
    kv("POSTGRES_DB", os.environ.get("POSTGRES_DB", "")),
    kv("POSTGRES_USER", os.environ.get("POSTGRES_USER", "")),
    kv("POSTGRES_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "")),
    kv("POSTGRES_HOST", os.environ.get("POSTGRES_HOST", "postgres")),
    kv("POSTGRES_PORT", os.environ.get("POSTGRES_PORT", "5432")),
    kv("POSTGRES_HOST_PORT", os.environ.get("POSTGRES_HOST_PORT", "5432")),
    "",
    "# ── Redis ─────────────────────────────────────────────────────────────────",
    "REDIS_URL=redis://redis:6379/0",
    "",
]

email_host = os.environ.get("EMAIL_HOST", "")
if email_host:
    lines += [
        "# ── Email (SMTP) ──────────────────────────────────────────────────────────",
        kv("EMAIL_HOST", email_host),
        kv("EMAIL_PORT", os.environ.get("EMAIL_PORT", "587")),
        kv("EMAIL_USE_TLS", os.environ.get("EMAIL_USE_TLS", "True")),
        kv("EMAIL_HOST_USER", os.environ.get("EMAIL_HOST_USER", "")),
        kv("EMAIL_HOST_PASSWORD", os.environ.get("EMAIL_HOST_PASSWORD", "")),
        kv("DEFAULT_FROM_EMAIL", os.environ.get("DEFAULT_FROM_EMAIL", "")),
        "",
    ]

n8n_domain = os.environ.get("N8N_DOMAIN", "")
if n8n_domain:
    lines += [
        "# ── n8n ───────────────────────────────────────────────────────────────────",
        kv("N8N_DOMAIN", n8n_domain),
        kv("N8N_ENCRYPTION_KEY", os.environ.get("N8N_ENCRYPTION_KEY", "")),
        "",
        "# ── Integración Django ↔ n8n ──────────────────────────────────────────────",
        f"N8N_URL=https://{n8n_domain}",
        f"N8N_WEBHOOK_URL=https://{n8n_domain}/webhook/",
        "",
    ]

if os.environ.get("N8N_MCP_ENABLED") == "true":
    lines += [
        "# ── n8n-MCP ───────────────────────────────────────────────────────────────",
        "N8N_MCP_ENABLED=true",
        kv("N8N_MCP_AUTH_TOKEN", os.environ.get("N8N_MCP_AUTH_TOKEN", "")),
        "# Completa N8N_API_KEY después del primer inicio de n8n: Settings > API",
        "N8N_API_KEY=",
        "",
    ]

with open(".env", "w") as f:
    f.write("\n".join(lines) + "\n")
PYEOF

# ── Resumen ───────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Configuración completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Proyecto:    ${PROJECT_NAME}"
echo "  Django:      https://${DOMAIN}  (puerto ${APP_PORT})"
echo "  Admin URL:   https://${DOMAIN}/${ADMIN_URL}"
echo "  PostgreSQL:  ${POSTGRES_MODE} (${POSTGRES_HOST}:${POSTGRES_PORT})"
[ -n "${N8N_DOMAIN}" ] && echo "  n8n:         https://${N8N_DOMAIN}  (puerto ${N8N_PORT})"
[ "${N8N_MCP_ENABLED}" = "true" ] && echo "  n8n-MCP:     https://${N8N_DOMAIN}/mcp  (puerto ${N8N_MCP_PORT})"
echo ""
echo "Archivo .env generado correctamente."
echo ""
echo "━━━ Próximos pasos ━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Configura nginx (solo la primera vez):"
echo "     make nginx"
echo ""
echo "  2. Obtén certificado SSL con certbot:"
CERTBOT_DOMAINS="-d ${DOMAIN}"
[ -n "${N8N_DOMAIN}" ] && CERTBOT_DOMAINS="${CERTBOT_DOMAINS} -d ${N8N_DOMAIN}"
echo "     sudo certbot --nginx ${CERTBOT_DOMAINS}"
echo ""
echo "  3. Despliega la aplicación:"
echo "     make deploy"
echo ""
[ "${POSTGRES_MODE}" = "host" ] && echo "  NOTA: PostgreSQL en host — configura pg_hba.conf antes de hacer deploy."
[ "${N8N_MCP_ENABLED}" = "true" ] && echo "  NOTA: Completa N8N_API_KEY en .env después del primer inicio de n8n."
echo ""
