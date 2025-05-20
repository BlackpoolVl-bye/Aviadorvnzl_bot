import websocket
import json

def on_message(ws, message):
    # Procesa los datos recibidos (ej: multiplicador de Aviator)
    data = json.loads(message)
    if "crash_point" in data:  # Ejemplo de campo (ajusta según lo que veas en Chrome)
        print(f"Multiplicador actual: {data['crash_point']}X")

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada")

def on_open(ws):
    print("Conectado al WebSocket")

# URL del WebSocket (obtén esta URL desde las herramientas de desarrollador)
ws_url = "wss://cf.1win.direct/v4/socket.io/?Language=es&xorigin=1win.com&EIO=4&transport=websocket"  # Ejemplo para Blaze, ajusta según el casino

ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open = on_open
ws.run_forever()  # Mantén la conexión activa