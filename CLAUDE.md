# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Configuración inicial
```bash
make setup        # wizard interactivo que genera .env
```

### Desarrollo local
```bash
make install      # pip install -r requirements-dev.txt + tailwind install
make dev-up       # levanta Redis + PostgreSQL + n8n/MCP según .env (docker-compose.dev.yml)
make dev          # migrate + tailwind start (background) + runserver
make dev-down     # detiene los contenedores de desarrollo
make dev-logs     # logs de los contenedores de desarrollo
```

En desarrollo, Tailwind y Django se ejecutan en terminales separadas:
```bash
# Terminal 1
python manage.py tailwind start

# Terminal 2
python manage.py runserver
```

### Django
```bash
make migrate      # python manage.py migrate
make migrations   # python manage.py makemigrations
make superuser    # python manage.py createsuperuser
make collect      # collectstatic
make shell        # python manage.py shell
```

### n8n
```bash
make n8n-export   # exporta workflows de n8n dev a n8n/workflows/ (para commitear)
```

### Producción
```bash
make check-ports  # verifica disponibilidad de puertos antes de desplegar
make nginx        # configura nginx (SOLO la primera vez — no sobreescribir tras certbot)
make deploy       # git pull + verifica puertos + rebuild contenedores
make logs         # docker compose logs -f django
make down         # docker compose down
```

On Windows, `NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'` is set in settings.py inside the `if DEBUG:` block.

## Architecture

Single `core/settings.py` — no separate dev/prod files. Behavior adapts via environment variables:
- `DEBUG=True` → SQLite, console email, Tailwind + browser-reload enabled
- `POSTGRES_DB` defined → PostgreSQL
- `POSTGRES_MODE=host` → PostgreSQL en el servidor host (contenedores usan `host.docker.internal`)
- `EMAIL_HOST` defined → SMTP backend
- `DEBUG=False` → HSTS, secure CSRF, no dev tools

**Puertos consecutivos:** Django usa `APP_PORT` (default 8000), n8n `APP_PORT+1` (8001), n8n-MCP `APP_PORT+2` (8002). En producción todos los puertos bindean a `127.0.0.1` — solo accesibles via nginx.

**Tailwind setup** (`django-tailwind` + Tailwind CSS v4 + DaisyUI v5):
- Source CSS: `theme/static_src/src/styles.css`
- Output CSS: `theme/static/css/dist/styles.css`
- `{% load tailwind_tags %}` + `{% tailwind_css %}` in `templates/base.html`
- When adding new Django apps, add `@source "../../../<app_name>"` to `styles.css`

**Static files:** `CompressedManifestStaticFilesStorage` (Whitenoise) genera hashes en filenames y archivos `.gz`. nginx sirve `/static/` directamente con `gzip_static on` para usar los `.gz` pre-generados. Cache `immutable` es seguro porque los filenames cambian con cada deploy.

**Redis:** Siempre activo (contenedor). Cache compartido entre workers Gunicorn, sesiones via cache (no DB), django-axes usa cache en vez de DB.

**Security:** django-axes (brute-force lockout, 5 intentos, 1h cooldown, backend cache), django-csp (CSP headers), HSTS en producción.

**Admin URL** is randomized via `ADMIN_URL` env var. Exposed in `robots.txt` via template context.

**Docker Compose profiles:**
- `postgres` — PostgreSQL contenedor (solo cuando `POSTGRES_MODE=container`, default)
- `n8n` — n8n automation (cuando `N8N_DOMAIN` está definido)
- `n8n-mcp` — n8n MCP server (cuando `N8N_MCP_ENABLED=true` y n8n habilitado)
- Redis y Django siempre se ejecutan (sin profile)

**n8n (opcional):**
- Subdominio propio (`N8N_DOMAIN`), imagen custom con Python 3.12 (`docker/n8n.Dockerfile`)
- Comparte PostgreSQL con DB separada (`n8n`), creada por `docker/init-db.sql`
- Workflows exportados con `make n8n-export` → `n8n/workflows/`, importados automáticamente en prod
- `N8N_ENCRYPTION_KEY` debe mantenerse constante — cambiarla invalida credenciales

**n8n-MCP (opcional):**
- `ghcr.io/czlonkowski/n8n-mcp:latest` en modo HTTP
- Requiere n8n funcionando y saludable
- Accesible via nginx en `https://N8N_DOMAIN/mcp`
- Requiere `N8N_API_KEY` (generar en n8n Settings > API) y `N8N_MCP_AUTH_TOKEN`

**nginx:** Solo se configura una vez con `make nginx`. NO ejecutar en cada deploy — certbot modifica el archivo para SSL y sobreescribirlo eliminaria los certificados.

**Production:** Docker Compose + Gunicorn (`entrypoint.sh`) + Nginx en host. `deploy.sh` hace git pull + verifica puertos + construye profiles dinámicamente según `.env` + rebuild contenedores.
