import os
import json
import time
import logging
import threading
import asyncio
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import websocket
import telegram
from telegram.ext import Application, CommandHandler

# --- Configuración Inicial ---
load_dotenv()  # Carga variables de .env

TOKEN = os.getenv('8003841250:AAHhSeVuAvuPYpOzucRZMgu8xoAz9x-TadM')
print(f"Token cargado: {TOKEN}")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aviator_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Constantes ---
class Config:
    TELEGRAM_TOKEN = os.getenv('8003841250:AAHhSeVuAvuPYpOzucRZMgu8xoAz9x-TadM')
    CHAT_ID = os.getenv('1985047351')
    WS_URL = os.getenv('WS_URL', 'wss://cf.1win.direct/v4/socket.io/?Language=es&xorigin=1win.com&EIO=4&transport=websocket')
    SOCKS_PROXY = os.getenv('socks5://192.252.216.81:4145')  # Ej: 127.0.0.1:9050
    PREDICTION_THRESHOLD = float(os.getenv('PREDICTION_THRESHOLD', 2.0))
    API_KEY = os.getenv('8003841250:AAHhSeVuAvuPYpOzucRZMgu8xoAz9x-TadM')

# --- Clases Principales ---
class AviatorAnalyzer:
    def _init_(self):
        self.historical_data = []
        self.last_alert = None

    def add_data_point(self, crash_point):
        """Guarda datos y analiza patrones"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'crash': float(crash_point)
        }
        self.historical_data.append(entry)
        
        # Guardar cada 10 registros
        if len(self.historical_data) % 10 == 0:
            self.save_to_csv()
        
        return self.check_alert(crash_point)

    def check_alert(self, crash_point):
        """Determina si enviar alerta"""
        if crash_point >= Config.PREDICTION_THRESHOLD:
            return f"🚨 ALERTA: Crash alto {crash_point}X"
        
        # Análisis de tendencia (últimos 5 datos)
        if len(self.historical_data) >= 5:
            last_5 = [x['crash'] for x in self.historical_data[-5:]]
            avg = sum(last_5) / len(last_5)
            if avg < 1.3:
                return "📉 Tendencia bajista detectada"
        return None

    def save_to_csv(self):
        """Persistencia de datos"""
        try:
            df = pd.DataFrame(self.historical_data)
            df.to_csv('/data/history.csv', index=False, mode='a')
        except Exception as e:
            logger.error(f"Error guardando CSV: {e}")

class AviatorWebSocket:
    def _init_(self, analyzer):
        self.analyzer = analyzer
        self.ws = None
        self.reconnect_delay = 5

    def start(self):
        """Inicia conexión WebSocket"""
        ws_options = {
            'on_message': self.on_message,
            'on_error': self.on_error,
            'on_close': self.on_close,
            'on_open': self.on_open
        }

        if Config.SOCKS_PROXY:
            ws_options['http_proxy_host'] = Config.SOCKS_PROXY.split(':')[1][2:]
            ws_options['http_proxy_port'] = int(Config.SOCKS_PROXY.split(':')[2])
            logger.info(f"Usando proxy: {Config.SOCKS_PROXY}")

        self.ws = websocket.WebSocketApp(Config.WS_URL, **ws_options)
        
        while True:
            try:
                self.ws.run_forever(
                    ping_interval=30,
                    ping_timeout=10
                )
            except Exception as e:
                logger.error(f"Error WS: {e}")
            time.sleep(self.reconnect_delay)

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if crash_point := data.get('crash'):
                if alert := self.analyzer.add_data_point(crash_point):
                    TelegramBot.send_alert(alert)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")

    def on_error(self, ws, error):
        logger.error(f"WS Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"WS Cerrado. Reconectando en {self.reconnect_delay}s...")

    def on_open(self, ws):
        logger.info("Conexión WS establecida")

class TelegramBot:
    bot = telegram.Bot(token=Config.TELEGRAM_TOKEN)

    @classmethod
    async def send_alert(cls, message):
        """Envía mensaje a Telegram con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await cls.bot.send_message(
                    chat_id=Config.CHAT_ID,
                    text=message,
                    parse_mode='Markdown'
                )
                break
            except Exception as e:
                logger.error(f"Error enviando alerta (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

    @classmethod
    async def start(cls, update, context):
        """Maneja el comando /start"""
        await update.message.reply_text(
            "🤖 Bot Aviator Activo\n"
            f"- Umbral alerta: {Config.PREDICTION_THRESHOLD}X\n"
            "Envía /estadisticas para ver datos",
            parse_mode='Markdown'
        )

    @classmethod
    async def stats(cls, update, context):
        """Maneja el comando /estadisticas"""
        if analyzer.historical_data:
            last_5 = [x['crash'] for x in analyzer.historical_data[-5:]]
            msg = "📊 Últimos 5 crashes:\n" + "\n".join(f"{x}X" for x in last_5)
        else:
            msg = "No hay datos aún"
        await update.message.reply_text(msg)

# --- Inicialización ---
analyzer = AviatorAnalyzer()

async def main():
    """Punto de entrada principal"""
    # Iniciar WebSocket en segundo plano
    ws_thread = threading.Thread(
        target=AviatorWebSocket(analyzer).start,
        daemon=True
    )
    ws_thread.start()

    # Configurar bot de Telegram
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", TelegramBot.start))
    application.add_handler(CommandHandler("estadisticas", TelegramBot.stats))
    
    logger.info("Bot iniciado correctamente")
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot detenido manualmente")
    except Exception as e:
        logger.critical(f"Error crítico: {e}")