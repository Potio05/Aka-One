import os
import subprocess
import logging
import requests
from typing import Optional, Dict, Any
# Google GenAI SDK (assuming 'google-genai' and 'google-api-python-client' are installed, or we use requests for simplicity)
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# --- WEB SEARCH TOOL ---
def web_search(query: str) -> str:
    """
    Perform a Google Custom Search to find information on the web.
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID mapped in environment.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        return "[Error] GOOGLE_API_KEY or GOOGLE_CSE_ID not configured."
        
    try:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=3).execute()
        
        results = ""
        for item in res.get('items', []):
            results += f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\nLink: {item.get('link')}\n\n"
            
        return results if results else "No results found."
    except Exception as e:
        logger.error(f"Web Search Error: {e}")
        return f"[Error] {e}"

# --- CODE EDITOR TOOL ---
def read_source_code(filepath: str) -> str:
    """Read the content of a local source file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Error] Cannot read file {filepath}: {e}"

def write_source_code(filepath: str, content: str) -> str:
    """Overwrite a local source file with new content."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully updated {filepath}"
    except Exception as e:
        return f"[Error] Cannot write to file {filepath}: {e}"

# --- NODE COMMUNICATION TOOL ---
NODE_REGISTRY = {
    # This should dynamically populate in a real scenario
    "PC-1": "http://localhost:8081",
    "PC-2": "http://localhost:8082" 
}

def send_command_to_pc(pc_id: str, command: str) -> str:
    """
    Send a terminal command (CMD/PowerShell) to a specific remote node.
    WARNING: Highly sensitive RCE function.
    """
    node_url = NODE_REGISTRY.get(pc_id)
    if not node_url:
        return f"[Error] Unknown PC ID: {pc_id}. Available nodes: {list(NODE_REGISTRY.keys())}"
        
    try:
        logger.info(f"Sending command to {pc_id}: {command}")
        # Assuming the node has an endpoint /execute
        response = requests.post(
            f"{node_url}/execute", 
            json={"command": command},
            timeout=30 # 30 seconds wait for command completion
        )
        
        if response.status_code == 200:
            data = response.json()
            return f"Stdout:\n{data.get('stdout')}\nStderr:\n{data.get('stderr')}"
        else:
            return f"[Error] Node returned status {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
         return f"[Error] Could not connect to {pc_id} at {node_url}. Is the node running?"
    except Exception as e:
        return f"[Error] Failed to communicate with {pc_id}: {e}"

# Optional: Local execution for testing without nodes
def execute_local_command(command: str) -> str:
    """Execute a command on the central brain server directly."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}"
    except Exception as e:
        return f"[Error] Execution failed: {e}"
