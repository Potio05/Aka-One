import websocket

try:
    print("Testing WebSocket connection to ws://100.80.201.113:8000/ws/debug_test ...")
    ws = websocket.WebSocket()
    ws.connect("ws://100.80.201.113:8000/ws/debug_test", timeout=5)
    print("WebSocket connected successfully!")
    ws.close()
except Exception as e:
    print("WebSocket connection failed:", e)
