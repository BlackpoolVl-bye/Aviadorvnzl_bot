import telegram
from telegram.ext import Application, CommandHandler
import websocket
import json
import threading
import pandas as pd
from datetime import datetime
import asyncio
import logging
import os
import time

# Configuración desde variables de entorno
TELEGRAM_TOKEN = os.getenv('8003841250:AAHhSeVuAvuPYpOzucRZMgu8xoAz9x-TadM')
CHAT_ID = os.getenv('1985047351')
PREDICTION_THRESHOLD = float(os.getenv('PREDICTION_THRESHOLD', 2.0))
WS_URL = os.getenv('WS_URL', 'wss://cf.1win.direct/v4/socket.io/?Language=es&xorigin=1win.com&EIO=4&transport=websocket')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ws = websocket.WebSocketApp(
    "wss://cf.1win.direct/v4/socket.io/?Language=es&xorigin=1win.com&EIO=4&transport=websocket",
    #ACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA#
    socks_proxy="socks5://5.161.103.41"
)
# Bot y datos
bot = telegram.Bot(token=TELEGRAM_TOKEN)
historical_data = []

async def send_alert(message):
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error enviando alerta: {e}")

def websocket_thread():
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if crash := data.get('crash'):
                historical_data.append({
                    'timestamp': datetime.now().isoformat(),
                    'crash': float(crash)
                })
                
                if float(crash) >= PREDICTION_THRESHOLD:
                    asyncio.run(send_alert(f"🚨 Crash alto: {crash}X"))
                
                # Guardar datos cada 10 registros
                if len(historical_data) % 10 == 0:
                    pd.DataFrame(historical_data).to_csv('/data/history.csv', index=False)
        
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")

    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_message=on_message,
                on_error=lambda ws, e: logger.error(f"WS Error: {e}"),
                on_close=lambda ws: logger.warning("WS Cerrado")
            )
            ws.run_forever(ping_interval=30)
        except Exception as e:
            logger.error(f"WS Reconectando: {e}")
            time.sleep(5)

async def start(update, context):
    await update.message.reply_text(
        "🤖 Bot Aviator Activo\n"
        f"- Umbral alerta: {PREDICTION_THRESHOLD}X\n"
        f"- Datos históricos: {len(historical_data)} registros",
        parse_mode='Markdown'
    )

async def main():
    # Iniciar WebSocket en segundo plano
    threading.Thread(
        target=websocket_thread,
        daemon=True
    ).start()

    # Configurar bot de Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())