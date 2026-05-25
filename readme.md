# telegram-status-bot

A small, one-shot Linux status reporter that sends a clean plain-text system report to a Telegram chat.

This project is intentionally simple: it does not run as a daemon, does not receive Telegram commands, and does not require a database or scheduler. Run it manually, from cron, or as a one-shot Docker container.

---

## English

### What it does

`telegram-status-bot` collects basic Linux server metrics and sends them to Telegram as plain text.

Supported metrics:

- Server name.
- Local date and time.
- Uptime from `/proc/uptime`.
- CPU temperature when a Linux thermal sensor is available.
- RAM usage percentage from `/proc/meminfo`.
- Disk usage percentage for configured partitions.
- Partial errors when a metric or partition cannot be read.

Example output:

```text
Server: my-server
Time: 2026-05-25 10:30
Uptime: 4 days, 2 hours
CPU temperature: 48.2°C
RAM usage: 62.4%

Disks:
- /: 71.2% used (120.3 GB / 169.0 GB)
- /data: 83.8% used (838.0 GB / 1000.0 GB)

Alerts:
- Disk usage for /data is above 80.0% (83.8%).
```

### Features

- One-shot execution: perfect for cron or manual checks.
- Plain-text Telegram messages, with no Markdown or HTML formatting.
- English and Spanish reports through `REPORT_LANGUAGE=en` or `REPORT_LANGUAGE=es`.
- Config validation with clear startup errors.
- Safe dry-run mode that prints the report without touching Telegram.
- Graceful degradation for missing CPU temperature, unreadable partitions, or unavailable host paths.
- Docker support for local builds and Docker Hub usage.
- Minimal runtime dependency footprint.

### Requirements

- Linux target host.
- Python 3.10 or newer.
- A Telegram bot token and chat ID for normal sending mode.

Python 3.10+ is used because it is widely available on modern Linux distributions and Raspberry Pi OS, while keeping the code clean with modern type hints such as `str | None`.

Runtime dependencies:

```text
python-dotenv
```

Telegram delivery uses Python's standard library HTTP client, so no Telegram SDK is required.

### Local installation

```bash
git clone https://github.com/TheMogoalex/telegram-status-bot.git
cd telegram-status-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your own values:

```bash
nano .env
```

### Configuration with `.env`

Minimal `.env` example:

```env
TELEGRAM_BOT_TOKEN=123456789:replace-with-your-bot-token
TELEGRAM_CHAT_ID=123456789
SERVER_NAME=my-linux-server
REPORT_LANGUAGE=en
DISK_PARTITIONS=/,/data
DISK_USAGE_ALERT_PERCENT=80
RAM_USAGE_ALERT_PERCENT=85
CPU_TEMPERATURE_ALERT_CELSIUS=75
MIN_UPTIME_ALERT_MINUTES=10
HOST_ROOT=/
HOST_PROC=/proc
HOST_SYS=/sys
CPU_TEMPERATURE_PATH=
TELEGRAM_REQUEST_TIMEOUT_SECONDS=10
```

### Environment variables

| Variable | Required | Default | Description |
|---|---:|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes for normal mode | none | Telegram bot token used to send the message. Not required for `--dry-run`. |
| `TELEGRAM_CHAT_ID` | Yes for normal mode | none | Target Telegram chat ID or channel ID. Not required for `--dry-run`. |
| `SERVER_NAME` | Yes | none | Name shown at the top of the report. |
| `DISK_PARTITIONS` | No | `/` | Comma-separated absolute paths to report, for example `/,/data,/mnt/backup`. |
| `REPORT_LANGUAGE` | No | `en` | Report language. Supported values: `en`, `es`. |
| `DISK_USAGE_ALERT_PERCENT` | No | `80` | Alert when a configured disk is above this used percentage. Set to `0` to disable. |
| `RAM_USAGE_ALERT_PERCENT` | No | `85` | Alert when RAM usage is above this percentage. Set to `0` to disable. |
| `CPU_TEMPERATURE_ALERT_CELSIUS` | No | `75` | Alert when CPU temperature is above this value. Set to `0` to disable. |
| `MIN_UPTIME_ALERT_MINUTES` | No | `10` | Alert when uptime is below this value. Useful to detect recent reboots. Set to `0` to disable. |
| `HOST_ROOT` | No | `/` | Filesystem root used for disk checks. Use `/host` in Docker when mounting the host root. |
| `HOST_PROC` | No | `/proc` | Proc filesystem used for uptime and RAM metrics. Use `/host/proc` in Docker host mode. |
| `HOST_SYS` | No | `/sys` | Sys filesystem used for thermal sensors. Use `/host/sys` in Docker host mode. |
| `CPU_TEMPERATURE_PATH` | No | empty | Optional explicit absolute path to a temperature file. When empty, thermal zones under `HOST_SYS` are scanned. |
| `TELEGRAM_REQUEST_TIMEOUT_SECONDS` | No | `10` | HTTP timeout for Telegram delivery. |

### Run locally

Send a real Telegram report:

```bash
python main.py
```

Dry run without Telegram:

```bash
python main.py --dry-run
```

Use a specific env file:

```bash
python main.py --env-file /etc/telegram-status-bot.env
python main.py --dry-run --env-file /etc/telegram-status-bot.env
```

### Schedule with cron

Example: send one report every day at 09:00.

```bash
crontab -e
```

```cron
0 9 * * * cd /opt/telegram-status-bot && /opt/telegram-status-bot/.venv/bin/python main.py >> /var/log/telegram-status-bot.log 2>&1
```

Use absolute paths in cron because cron runs with a small environment.

### Docker: local build

Build the image locally:

```bash
docker build -t telegram-status-bot .
```

Run it as a one-shot container:

```bash
docker run --rm --env-file .env telegram-status-bot
```

Dry run:

```bash
docker run --rm --env-file .env telegram-status-bot --dry-run
```

### Docker: Docker Hub image

Use the published image name:

```bash
docker run --rm --env-file .env themogoalex/telegram-status-bot:latest
```

Dry run:

```bash
docker run --rm --env-file .env themogoalex/telegram-status-bot:latest --dry-run
```

### Docker host metrics

Without extra mounts, Docker may report container-visible metrics instead of the host's real metrics. For host reporting, mount the host root, `/proc`, and `/sys` read-only and point the bot to those paths:

```bash
docker run --rm \
  --env-file .env \
  -e HOST_ROOT=/host \
  -e HOST_PROC=/host/proc \
  -e HOST_SYS=/host/sys \
  -v /:/host:ro \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  themogoalex/telegram-status-bot:latest
```

With this setup, `DISK_PARTITIONS=/,/data` is resolved internally as `/host` and `/host/data`, but the report still displays `/` and `/data`.

Docker limitations:

- If `/proc` is not mounted from the host, uptime and RAM may describe the container namespace or may be unavailable.
- If `/sys` is not mounted from the host, CPU temperature may be unavailable.
- If `/` is not mounted as `/host`, disk checks may report the container filesystem instead of the host filesystem.
- The image runs as a non-root user. If a host path cannot be traversed because of permissions, either adjust the mount/path permissions or run the container with an explicit user suitable for your environment.

### Raspberry Pi notes

Raspberry Pi CPU temperature is commonly exposed at:

```text
/sys/class/thermal/thermal_zone0/temp
```

The bot does not assume that path always exists. It scans Linux thermal zones under `HOST_SYS` and reports `unavailable` if no readable sensor exists. You can force a specific file with `CPU_TEMPERATURE_PATH`.

### Tests and code quality

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

### License

This project is licensed under the MIT License.

### Author

Author: <https://github.com/themogoalex>
Linkedin: https://www.linkedin.com/in/alejandro-mogollo/

---

## Español

### Qué hace

`telegram-status-bot` recopila métricas básicas de un servidor Linux y las envía a Telegram como texto plano.

Métricas soportadas:

- Nombre del servidor.
- Fecha y hora local.
- Uptime desde `/proc/uptime`.
- Temperatura CPU si existe un sensor térmico Linux disponible.
- Porcentaje de uso de RAM desde `/proc/meminfo`.
- Porcentaje de uso de disco para particiones configuradas.
- Errores parciales cuando una métrica o partición no se puede leer.

Ejemplo de salida:

```text
Servidor: mi-servidor
Hora: 2026-05-25 10:30
Tiempo activo: 4 días, 2 horas
Temperatura CPU: 48.2°C
Uso de RAM: 62.4%

Discos:
- /: 71.2% usado (120.3 GB / 169.0 GB)
- /data: 83.8% usado (838.0 GB / 1000.0 GB)

Alertas:
- El uso de disco en /data supera el 80.0% (83.8%).
```

### Características

- Ejecución one-shot: ideal para cron o comprobaciones manuales.
- Mensajes de Telegram en texto plano, sin Markdown ni HTML.
- Informes en inglés y español mediante `REPORT_LANGUAGE=en` o `REPORT_LANGUAGE=es`.
- Validación de configuración con errores claros al arrancar.
- Modo seguro `--dry-run` que imprime el informe sin tocar Telegram.
- Degradación elegante si falta la temperatura CPU, una partición no existe o un path del host no está disponible.
- Soporte Docker con build local e imagen publicada.
- Dependencias runtime mínimas.

### Requisitos

- Host objetivo Linux.
- Python 3.10 o superior.
- Token de bot de Telegram y chat ID para el modo normal de envío.

Se usa Python 3.10+ porque está ampliamente disponible en distribuciones Linux modernas y Raspberry Pi OS, y permite mantener el código limpio con type hints modernos como `str | None`.

Dependencias runtime:

```text
python-dotenv
```

El envío a Telegram usa el cliente HTTP de la librería estándar de Python, así que no hace falta instalar un SDK de Telegram.

### Instalación local

```bash
git clone https://github.com/TheMogoalex/telegram-status-bot.git
cd telegram-status-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con tus valores:

```bash
nano .env
```

### Configuración con `.env`

Ejemplo mínimo de `.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:replace-with-your-bot-token
TELEGRAM_CHAT_ID=123456789
SERVER_NAME=my-linux-server
REPORT_LANGUAGE=es
DISK_PARTITIONS=/,/data
DISK_USAGE_ALERT_PERCENT=80
RAM_USAGE_ALERT_PERCENT=85
CPU_TEMPERATURE_ALERT_CELSIUS=75
MIN_UPTIME_ALERT_MINUTES=10
HOST_ROOT=/
HOST_PROC=/proc
HOST_SYS=/sys
CPU_TEMPERATURE_PATH=
TELEGRAM_REQUEST_TIMEOUT_SECONDS=10
```

### Variables de entorno

| Variable | Obligatoria | Default | Descripción |
|---|---:|---|---|
| `TELEGRAM_BOT_TOKEN` | Sí en modo normal | ninguno | Token del bot de Telegram usado para enviar el mensaje. No es necesaria en `--dry-run`. |
| `TELEGRAM_CHAT_ID` | Sí en modo normal | ninguno | Chat ID o channel ID de destino. No es necesaria en `--dry-run`. |
| `SERVER_NAME` | Sí | ninguno | Nombre mostrado al inicio del informe. |
| `DISK_PARTITIONS` | No | `/` | Paths absolutos separados por coma, por ejemplo `/,/data,/mnt/backup`. |
| `REPORT_LANGUAGE` | No | `en` | Idioma del informe. Valores soportados: `en`, `es`. |
| `DISK_USAGE_ALERT_PERCENT` | No | `80` | Alerta cuando un disco configurado supera este porcentaje de uso. Pon `0` para desactivar. |
| `RAM_USAGE_ALERT_PERCENT` | No | `85` | Alerta cuando la RAM supera este porcentaje de uso. Pon `0` para desactivar. |
| `CPU_TEMPERATURE_ALERT_CELSIUS` | No | `75` | Alerta cuando la temperatura CPU supera este valor. Pon `0` para desactivar. |
| `MIN_UPTIME_ALERT_MINUTES` | No | `10` | Alerta cuando el uptime está por debajo de este valor. Útil para detectar reinicios recientes. Pon `0` para desactivar. |
| `HOST_ROOT` | No | `/` | Raíz del filesystem usada para comprobar discos. Usa `/host` en Docker al montar la raíz del host. |
| `HOST_PROC` | No | `/proc` | Proc filesystem usado para uptime y RAM. Usa `/host/proc` en Docker en modo host. |
| `HOST_SYS` | No | `/sys` | Sys filesystem usado para sensores térmicos. Usa `/host/sys` en Docker en modo host. |
| `CPU_TEMPERATURE_PATH` | No | vacío | Path absoluto opcional a un archivo de temperatura. Si está vacío, se escanean thermal zones bajo `HOST_SYS`. |
| `TELEGRAM_REQUEST_TIMEOUT_SECONDS` | No | `10` | Timeout HTTP para enviar a Telegram. |

### Ejecución local

Enviar un informe real a Telegram:

```bash
python main.py
```

Modo prueba sin Telegram:

```bash
python main.py --dry-run
```

Usar un archivo env específico:

```bash
python main.py --env-file /etc/telegram-status-bot.env
python main.py --dry-run --env-file /etc/telegram-status-bot.env
```

### Ejecución programada con cron

Ejemplo: enviar un informe cada día a las 09:00.

```bash
crontab -e
```

```cron
0 9 * * * cd /opt/telegram-status-bot && /opt/telegram-status-bot/.venv/bin/python main.py >> /var/log/telegram-status-bot.log 2>&1
```

Usa paths absolutos en cron porque cron ejecuta con un entorno muy reducido.

### Docker: build local

Construir la imagen localmente:

```bash
docker build -t telegram-status-bot .
```

Ejecutarla como contenedor one-shot:

```bash
docker run --rm --env-file .env telegram-status-bot
```

Modo prueba:

```bash
docker run --rm --env-file .env telegram-status-bot --dry-run
```

### Docker: imagen en Docker Hub

Usar el nombre de imagen publicado:

```bash
docker run --rm --env-file .env themogoalex/telegram-status-bot:latest
```

Modo prueba:

```bash
docker run --rm --env-file .env themogoalex/telegram-status-bot:latest --dry-run
```

### Métricas del host con Docker

Sin mounts adicionales, Docker puede reportar métricas visibles desde el contenedor en lugar de las métricas reales del host. Para reportar el host, monta la raíz, `/proc` y `/sys` del host en modo solo lectura y apunta el bot a esos paths:

```bash
docker run --rm \
  --env-file .env \
  -e HOST_ROOT=/host \
  -e HOST_PROC=/host/proc \
  -e HOST_SYS=/host/sys \
  -v /:/host:ro \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  themogoalex/telegram-status-bot:latest
```

Con esta configuración, `DISK_PARTITIONS=/,/data` se resuelve internamente como `/host` y `/host/data`, pero el informe sigue mostrando `/` y `/data`.

Limitaciones de Docker:

- Si no montas `/proc` desde el host, uptime y RAM pueden describir el namespace del contenedor o no estar disponibles.
- Si no montas `/sys` desde el host, la temperatura CPU puede no estar disponible.
- Si no montas `/` como `/host`, los discos pueden corresponder al filesystem del contenedor en lugar del host.
- La imagen se ejecuta como usuario no root. Si un path del host no se puede recorrer por permisos, ajusta permisos/mounts o ejecuta el contenedor con un usuario adecuado para tu entorno.

### Notas sobre Raspberry Pi

En Raspberry Pi la temperatura CPU suele estar expuesta en:

```text
/sys/class/thermal/thermal_zone0/temp
```

El bot no asume que ese path exista siempre. Escanea thermal zones bajo `HOST_SYS` y reporta `no disponible` si no hay un sensor legible. Puedes forzar un archivo específico con `CPU_TEMPERATURE_PATH`.

### Tests y calidad de código

Instalar dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
```

Ejecutar tests:

```bash
pytest
```

Ejecutar linting:

```bash
ruff check .
```

### Licencia

Este proyecto está licenciado bajo la Licencia MIT.


### Autor

Autor: <https://github.com/themogoalex>
Linkedin: https://www.linkedin.com/in/alejandro-mogollo/
