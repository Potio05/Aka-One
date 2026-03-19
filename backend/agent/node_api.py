from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict

# --- CENTRAL NODE REGISTRY API (AKA-BRAIN) ---
# This API sits on the central server and keeps track of active nodes.

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory registry for simplicity. 
# Should use Redis or DB in production.
NODE_REGISTRY: Dict[str, str] = {
    # e.g., "PC-1": "http://192.168.1.10:8081"
}

class NodeRegistration(BaseModel):
    node_id: str
    ip_address: str
    port: int = 8081

@router.post("/register")
async def register_node(node: NodeRegistration):
    """Nodes call this on startup to register themselves with the Brain."""
    url = f"http://{node.ip_address}:{node.port}"
    NODE_REGISTRY[node.node_id] = url
    logger.info(f"Registered Node: {node.node_id} at {url}")
    return {"status": "registered", "node_id": node.node_id, "url": url}

@router.get("/nodes")
async def list_nodes():
    """Returns the list of currently registered and active nodes."""
    return {"nodes": NODE_REGISTRY}

@router.post("/deregister/{node_id}")
async def deregister_node(node_id: str):
    if node_id in NODE_REGISTRY:
        del NODE_REGISTRY[node_id]
        logger.info(f"Deregistered Node: {node_id}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Node not found.")
