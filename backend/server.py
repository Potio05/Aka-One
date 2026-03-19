import asyncio
import json
import logging
import uuid
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BrainServer")

app = FastAPI(title="AKA-BRAIN Server")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # Stores Futures for pending commands expected to return a result
        self.pending_commands: Dict[str, asyncio.Future] = {}
        self.os_info: Dict[str, str] = {} # Phase 3: Tracks the OS of the node

    async def connect(self, websocket: WebSocket, node_id: str):
        await websocket.accept()
        self.active_connections[node_id] = websocket
        logger.info(f"[+] Nouveau membre connecté : {node_id}")

    def disconnect(self, node_id: str):
        if node_id in self.active_connections:
            del self.active_connections[node_id]
            logger.info(f"[-] Membre déconnecté : {node_id}")

    async def send_personal_message(self, message: dict, node_id: str):
        if node_id in self.active_connections:
            await self.active_connections[node_id].send_json(message)
            logger.info(f"[->] Message envoyé à {node_id} (action: {message.get('action')})")
        else:
            raise Exception(f"Node {node_id} introuvable ou déconnecté.")

    async def send_and_wait(self, node_id: str, command: str, timeout: int = 60) -> dict:
        """Sends a command and waits for the client to return the result via WebSocket."""
        cmd_id = str(uuid.uuid4())
        payload = {
            "action": "cmd",
            "command": command,
            "command_id": cmd_id
        }
        
        # Create a future to block until the answer is received
        future = asyncio.get_event_loop().create_future()
        self.pending_commands[cmd_id] = future
        
        try:
            await self.send_personal_message(payload, node_id)
            # Wait for the client to process and reply
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            del self.pending_commands[cmd_id]
            raise Exception("Timeout : Le noeud n'a pas répondu à temps.")
        except Exception as e:
            if cmd_id in self.pending_commands:
                del self.pending_commands[cmd_id]
            raise e

    def resolve_command(self, cmd_id: str, result: Any):
        if cmd_id in self.pending_commands:
            future = self.pending_commands[cmd_id]
            if not future.done():
                future.set_result(result)
            del self.pending_commands[cmd_id]

manager = ConnectionManager()

@app.websocket("/ws/{node_id}")
async def websocket_endpoint(websocket: WebSocket, node_id: str):
    await manager.connect(websocket, node_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                action = payload.get("action")
                action_type = payload.get("action_type")
                
                # Phase 3 : Register OS
                if action == "register":
                    manager.os_info[node_id] = payload.get("os", "Unknown")
                    logger.info(f"[*] Node {node_id} enregistré (OS: {manager.os_info[node_id]})")
                    
                # Phase 1.3 : Handle command result from Node
                elif action_type == "cmd_result":
                    cmd_id = payload.get("command_id")
                    result = payload.get("result")
                    logger.info(f"[<-] Résultat de {node_id} pour {cmd_id}.")
                    manager.resolve_command(cmd_id, result)
                    
            except json.JSONDecodeError:
                logger.error(f"[!] Invalid JSON reçu de {node_id}")
    except WebSocketDisconnect:
        manager.disconnect(node_id)
    except Exception as e:
        logger.error(f"[!] Erreur inattendue pour {node_id}: {e}")
        manager.disconnect(node_id)

# Expose loop for the Agent thread
@app.on_event("startup")
async def startup_event():
    # Start the NOC Network Monitor
    from backend.services.network_monitor import monitor
    monitor.start()
    
    # Save reference to the main thread's asyncio loop
    app.state.loop = asyncio.get_running_loop()
    from backend.agent_brain import init_agent
    init_agent(app.state.loop, manager)

from pydantic import BaseModel
class ChatRequest(BaseModel):
    query: str

@app.post("/agent_task")
async def trigger_agent(req: ChatRequest):
    """Entrypoint to ask the autonomous Agent to do something."""
    from backend.agent_brain import process_query_async
    try:
        response = await process_query_async(req.query)
        return {"status": "success", "response": response}
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
