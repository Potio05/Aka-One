import websocket
import json
import time
import subprocess
import os
import platform
import logging
from typing import Dict, Any

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NodeDaemon")

# In production, replace this with the Central Server's static IP
SERVER_IP = "100.80.201.113" # Tailscale IP du Serveur Ubuntu
SERVER_PORT = 8000
NODE_ID = f"PC-{platform.node()}"

# To handle reconnections robustly
def get_os_info() -> str:
    return platform.system()

def execute_command(command: str) -> Dict[str, Any]:
    """Exécute une commande système via subprocess.run"""
    logger.info(f"[*] Exécution de la commande : {command}")
    try:
        # shell=True est nécessaire pour exécuter des commandes brutes
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60 # Timeout de sécurité pour éviter le blocage
        )
        return {
            "status": "success",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        logger.error("[!] Erreur: Commande expirée (Timeout).")
        return {"status": "error", "message": "Timeout."}
    except Exception as e:
        logger.error(f"[!] Erreur critique d'exécution : {e}")
        return {"status": "error", "message": str(e)}

def on_message(ws, message):
    """Callback appelé lors de la réception d'un payload depuis le serveur."""
    logger.info(f"[<-] Message reçu du Cerveau : {message}")
    try:
        payload = json.loads(message)
        
        # Le Cerveau envoie toujours un dictionnaire avec "action"
        if payload.get("action") == "cmd":
            command = payload.get("command")
            cmd_id = payload.get("command_id", "unknown")
            
            if command:
                # Exécution réelle de la commande (Étape 1.3: Ping-Pong)
                execution_result = execute_command(command)
                
                # Formatage de la réponse pour le serveur
                response_payload = {
                    "action_type": "cmd_result",
                    "command_id": cmd_id,
                    "original_command": command,
                    "result": execution_result
                }
                
                # Renvoi du résultat via la socket
                ws.send(json.dumps(response_payload))
                logger.info(f"[->] Résultat envoyé avec succès pour cmd_id {cmd_id}.")
            else:
                 logger.warning("Action 'cmd' reçue mais le champ 'command' est vide.")
        else:
            logger.warning(f"Action non reconnue : {payload.get('action')}")
            
    except json.JSONDecodeError:
         logger.error("Message invalid (not JSON).")
    except Exception as e:
         logger.error(f"Erreur inattendue dans on_message : {e}")

def on_error(ws, error):
    logger.error(f"[X] Erreur WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.warning("[-] Connexion fermée. Tentative de reconnexion dans 5 secondes...")
    time.sleep(5)
    connect_to_brain() # Boucle de résilience infinie

def on_open(ws):
    logger.info(f"[+] Connecté avec succès au Cerveau Central ({SERVER_IP}). Identifiant: {NODE_ID}")
    
    # Envoi du message d'initialisation (utile pour la Phase 3 : Connaissance de l'OS)
    init_payload = {
        "action": "register",
        "os": get_os_info(),
        "node_id": NODE_ID
    }
    ws.send(json.dumps(init_payload))

def connect_to_brain():
    """Démarre le WebSocket Client de manière persistante."""
    ws_url = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/{NODE_ID}"
    logger.info(f"Tentative de connexion à {ws_url}...")
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    
    # run_forever écoute indéfiniment
    ws.run_forever()

if __name__ == "__main__":
    connect_to_brain()
