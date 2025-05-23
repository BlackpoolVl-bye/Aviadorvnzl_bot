FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos
COPY requirements.txt .
COPY aviator_bot.py .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Crear volumen para datos
RUN mkdir /data
VOLUME /data

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV TELEGRAM_TOKEN="8003841250:AAHhSeVuAvuPYpOzucRZMgu8xoAz9x-TadM"
ENV CHAT_ID="1985047351"
ENV WS_URL="wss://cf.1win.direct/v4/socket.io/?Language=es&xorigin=1win.com&EIO=4&transport=websocket"
ENV SOCKS_PROXY="socks5://192.252.216.81:4145"
ENV PREDICTION_THRESHOLD=2.0

CMD ["python", "aviator_bot.py"]