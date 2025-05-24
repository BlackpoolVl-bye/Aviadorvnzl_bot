import telebot
from telebot import types
import websocket
import requests
import json
import threading
import time
import re
import ssl

# CONEXIÓN CON NUESTRO BOT (considera usar variables de entorno para el token)
TOKEN = '7740960612:AAGDeYoqirZAUcN6IEpwxHu7p9tiiUki0_M'
API_KEY = 'wss://app-demo.spribe.io/BlueBox/websocket'

bot = telebot.TeleBot(TOKEN)
BASE_URL = 'https://1win.com/casino/play/aviator'

# Variables globales
ultimos_crashes = []
ws_connected = False
last_update = None

def connect_websocket():
    global ws_connected
    
    def on_message(ws, message):
        try:
            if 'round/update' in message:
                match = re.search(r'\["round/update",(.+)\]', message)
                if match:
                    round_data = json.loads(match.group(1))
                    if 'history' in round_data:
                        global ultimos_crashes
                        ultimos_crashes = [x['crash'] for x in round_data['history'] if x.get('crash')]
                        print(f"Datos actualizados: {ultimos_crashes[-3:]}")
        except Exception as e:
            print(f"Error procesando mensaje: {e}")

    def on_error(ws, error):
        print(f"Error WebSocket: {error}")

    def on_close(ws, close_status_code, close_msg):
        global ws_connected
        ws_connected = False
        print(f"Conexión cerrada. Código: {close_status_code}, Mensaje: {close_msg}")
        time.sleep(5)
        reconnect_websocket()

    def on_open(ws):
        global ws_connected
        ws_connected = True
        print("Conexión establecida")
        # Protocolo Socket.IO
        ws.send('40')
        ws.send('42["subscribe",{"name":"round"}]')

    def reconnect_websocket():
        print("Intentando reconexión...")
        connect_websocket()

    ws_url = "wss://app-demo.spribe.io/BlueBox/websocket"
    
    # Configuración especial con headers y SSL
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
        header={
            "Origin": "https://1win.com/casino/play/aviator",
            "User-Agent": "Mozilla/5.0"
        }
    )
    
    ws.run_forever(
        ping_interval=20,
        ping_timeout=10,
        sslopt={"cert_reqs": ssl.CERT_NONE}
    )
    # Iniciar conexión en segundo plano
websocket_thread = threading.Thread(target=connect_websocket, daemon=True)
websocket_thread.start()

@bot.message_handler(commands=['startt'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔄 Obtener Datos'))
    
    status = "✅ Conectado" if ws_connected else "❌ Desconectado"
    
    bot.send_message(
        message.chat.id,
        f"🔮 Bot Aviator 1win\n\n"
        f"Estado: {status}\n"
        f"Últimos datos: {ultimos_crashes[-3:] if ultimos_crashes else 'Ninguno'}",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == '🔄 Obtener Datos')
def send_data(message):
    if not ultimos_crashes:
        bot.send_message(message.chat.id, "⚠️ Esperando datos del servidor...")
        return
    
    # Análisis simple
    avg = sum(ultimos_crashes[-3:])/3 if len(ultimos_crashes) >=3 else 0
    tendencia = "↑ ALTA" if avg >= 2 else "↓ BAJA"
    
    respuesta = (
        "📊 Últimos resultados 1win:\n\n" +
        "\n".join([f"Ronda {i+1}: {crash}x" for i, crash in enumerate(ultimos_crashes[-5:])]) +
        f"\n\n• Tendencia: {tendencia}\n" +
        f"• Promedio: {avg:.2f}x"
    )
    
    bot.send_message(message.chat.id, respuesta)

# CREACIÓN DE COMANDO /START Y /HELP
@bot.message_handler(commands=['start'])
def send_welcomee(message):
    bot.reply_to(message, '¡Hola! Bienvenido al bot.')


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Puedes interactuar conmigo usando estos comandos:
/start - Inicia el bot
/help - Muestra esta ayuda
/pizza - Pregunta sobre tus preferencias de pizza
/foto - Lo que te gusta
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['pizza'])
def send_option(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Creación de botones
    btn_si = types.InlineKeyboardButton('Sí', callback_data='pizza_si')
    btn_no = types.InlineKeyboardButton('No', callback_data='pizza_no')
    
    # Agregar botones
    markup.add(btn_si, btn_no)
    
    # Enviar mensaje con los botones
    bot.send_message(message.chat.id,"¿Te gusta la pizza?", reply_markup=markup)
    bot.reply_to(message, text='')


@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    if call.data == 'pizza_si':
        bot.answer_callback_query(call.id, '¡A mí también me encanta! 🍕')
    elif call.data == 'pizza_no':
        bot.answer_callback_query(call.id, 'Bueno, cada uno con sus gustos.')
    # Puedes añadir más respuestas aquí si agregas más botones

#imagenes

@bot.message_handler(commands=['foto'])
def send_image(message):
    img_url = 'https://st.depositphotos.com/2778793/3943/v/450/depositphotos_39438137-stock-illustration-vintage-pop-middle-finger-up.jpg'
    bot.send_photo(chat_id=message.chat.id, photo=img_url, caption='Lo que te gusta')


if __name__ == "__main__":
    print("Bot iniciado...")
    bot.polling(non_stop=True)
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error en polling: {e}")
            time.sleep(5)