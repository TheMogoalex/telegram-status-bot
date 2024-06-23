# System Information Telegram Bot

## English

This project is a Telegram bot that retrieves and sends system information including CPU temperature, disk usage, uptime, and current time to a specified chat. The bot uses various system commands and libraries to gather this information and formats it before sending it to the Telegram chat.

### Features
- Fetches current system uptime.
- Reads CPU temperature.
- Retrieves current date and time.
- Checks disk usage for specified partitions.
- Sends the formatted information to a specified Telegram chat.

### Requirements
- Python 3.x
- Telegram Bot Token
- Python Libraries: `python-telegram-bot`, `python-dotenv`, `psutil`

### Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/yourusername/system-info-telegram-bot.git
   cd system-info-telegram-bot
   ´´´

2. Create and activate a virtual environment (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ´´´

3. Install the required libraries:
    ```sh
    pip install -r requirements.txt
   ´´´

4. Create a .env file in the root directory and add your Telegram bot token, chat ID, server name, and partitions:
    ```env
    TOKEN=your_telegram_bot_token
    CHAT_ID=your_chat_id
    SERVER_NAME=YourServerName
    PARTITIONS=/, /media/pi
   ´´´

5. Run the bot:
    ```sh
    python3 main.py
   ´´´

### Scheduled Execution with Cron
It is recommended to run this bot at regular intervals using cron. You can set up a cron job to execute the bot script at your desired intervals (e.g., every day at 10 a.m).

1. Open your crontab file:
   ```sh
    crontab -e
   ´´´

2. Add the following line to schedule the script to run every day at 10 a.m.:
    ```sh
    0 10 * * * /path/virtualenv/bin/python /path/main.py
    ´´´

## Español

Este proyecto es un bot de Telegram que recupera y envía información del sistema, incluida la temperatura de la CPU, el uso del disco, el tiempo de actividad y la hora actual a un chat especificado. El bot utiliza varios comandos del sistema y bibliotecas para recopilar esta información y la formatea antes de enviarla al chat de Telegram.

### Funcionalidades
- Obtiene el tiempo de actividad actual del sistema.
- Lee la temperatura de la CPU.
- Recupera la fecha y hora actual.
- Verifica el uso del disco para particiones especificadas.
- Envía la información formateada a un chat de Telegram especificado.

### Requisitos
- Python 3.x
- Token de un bot de Telegram
- Bibliotecas de Python: `python-telegram-bot`, `python-dotenv`, `psutil`

### Installation

1. Clona este repositorio:
   ```sh
   git clone https://github.com/yourusername/system-info-telegram-bot.git
   cd system-info-telegram-bot
   ´´´

2. Crea y activa un entorno virtual (opcional pero recomendado):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ´´´

3. Instala las bibliotecas requeridas:
    ```sh
    pip install -r requirements.txt
   ´´´

4. Crea un archivo .env en el directorio raíz y agrega el token de tu bot de Telegram, el ID del chat, el nombre del servidor y las particiones:
    ```env
    TOKEN=your_telegram_bot_token
    CHAT_ID=your_chat_id
    SERVER_NAME=YourServerName
    PARTITIONS=/, /media/pi
   ´´´

5. Ejecuta el bot:
    ```sh
    python3 main.py
   ´´´

### Ejecución Programada con Cron
Se recomienda ejecutar este bot a intervalos regulares usando cron. Puedes configurar un trabajo cron para ejecutar el script del bot en los intervalos deseados (por ejemplo, todos los días a las 10 a.m.).

1. Abre tu archivo crontab:
   ```sh
    crontab -e
   ´´´

2. Añade la siguiente línea para programar el script para que se ejecute todos los días a las 10 a.m.:
    ```sh
    0 10 * * * /path/virtualenv/bin/python /path/main.py
    ´´´
