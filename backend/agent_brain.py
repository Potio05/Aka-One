import os
import sys
import asyncio
import importlib
import logging
import urllib.request
import json
import ollama
from ollama import Client
from dotenv import load_dotenv

logger = logging.getLogger("AgentBrain")

# Loaded from the startup script of server.py
SERVER_LOOP = None
WS_MANAGER = None

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")
os.makedirs(SKILLS_DIR, exist_ok=True)


def init_agent(loop, manager):
    global SERVER_LOOP, WS_MANAGER
    SERVER_LOOP = loop
    WS_MANAGER = manager
    logger.info("Agent Brain initialized with references to Server Loop and WS Manager.")

# --- THE TOOLS (Function Calling) ---

# Llama 3.1 native function calling compatibility mapping for tools.
# Tools are kept exactly the same for dynamic plugin architecture!
def lister_noeuds() -> str:
    """Gets the list of currently connected computers (nodes) on the network."""
    if not WS_MANAGER:
        return "Erreur: WS_MANAGER non initialisé."
    nodes = list(WS_MANAGER.active_connections.keys())
    if not nodes:
        return "Aucun PC n'est connecté actuellement."
    return f"PCs connectés : {', '.join(nodes)}"

def verifier_etat_reseau() -> str:
    """Performs a network ping test to check the latency of the local router and internet (8.8.8.8). Use this whenever the user asks for a ping or network status."""
    from backend.services.network_monitor import NETWORK_STATUS
    res = "Statut Réseau (NOC) :\n"
    for target, info in NETWORK_STATUS.items():
        res += f"- {target} : {info['status']} (Latence: {info['latency']}, Dernier check: {info.get('last_checked', 'N/A')})\n"
    return res

def rechercher_logiciel(nom: str) -> str:
    """Searches the internet for software installation instructions or bash/powershell commands."""
    logger.info(f"Outil appelé: rechercher_logiciel({nom})")
    return f"Résultat: '{nom}' (Il est conseillé d'utiliser winget sur Windows ou apt-get sur Linux)."

def executer_sur_pc(id_pc: str, commande: str) -> str:
    """Executes a terminal native command (like bash, ping, ipconfig) on a specific remote PC."""
    if not WS_MANAGER or not SERVER_LOOP:
        return "[Erreur] Serveur WebSocket non initialisé."
        
    logger.info(f"Outil appelé: executer_sur_pc({id_pc}, '{commande}')")
    
    future = asyncio.run_coroutine_threadsafe(
        WS_MANAGER.send_and_wait(id_pc, commande),
        SERVER_LOOP
    )
    
    try:
        result = future.result(timeout=60)
        status = result.get("status")
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        return f"Status: {status}\nStdout: {stdout}\nStderr: {stderr}"
    except Exception as e:
        return f"[Erreur lors de l'exécution]: {e}"

def memoriser_information(sujet: str, contenu: str) -> str:
    """Saves an important rule, password, or system fact permanently into the AGI's Long-Term Vector Memory (Qdrant). Use this when the user asks you to remember something."""
    from backend.services.memory import memory
    logger.info(f"Outil appelé: memoriser_information({sujet})")
    success = memory.memorize(sujet, contenu)
    return "Information mémorisée avec succès dans la base vectorielle à long terme." if success else "Échec de la mémorisation (Qdrant injoignable)."

def consulter_memoire(requete_recherche: str) -> str:
    """Searches the AGI's Long-Term Memory (Qdrant) to recall rules, passwords, network IPs, or system facts relevant to the query. Use this if you don't know something about the infrastructure."""
    from backend.services.memory import memory
    logger.info(f"Outil appelé: consulter_memoire({requete_recherche})")
    return memory.recall(requete_recherche)

# --- ARCHITECTURE DES PLUGINS (Phase 4) ---

DYNAMIC_TOOLS = [lister_noeuds, verifier_etat_reseau, rechercher_logiciel, executer_sur_pc, memoriser_information, consulter_memoire]

def create_skill(nom: str, code_python: str) -> str:
    """Dynamically creates and compiles a new Python tool/skill. The Python code must contain a function with the exact same name as 'nom'."""
    filepath = os.path.join(SKILLS_DIR, f"{nom}.py")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_python)
            
        module_name = f"backend.skills.{nom}"
        
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
            action_desc = "rechargé"
        else:
            module = importlib.import_module(module_name)
            action_desc = "importé"
            
        if hasattr(module, nom):
            func = getattr(module, nom)
            if func.__name__ not in [t.__name__ for t in DYNAMIC_TOOLS]:
                DYNAMIC_TOOLS.append(func)
            return f"Succès: Le skill '{nom}' a été ajouté ! Tu peux l'utiliser maintenant."
        else:
            return f"Erreur: Le code ne contient pas la fonction '{nom}'."
    except Exception as e:
        return f"Erreur critique: {e}"

# --- SYSTEM PROMPT & AGENT LOOP ---

SYSTEM_PROMPT = """
You are the autonomous NOC System Administrator of AKA-ONE.
DO NOT SIMULATE OR FAKE RESULTS. DO NOT HALLUCINATE PING RESPONSES. 
YOU MUST ALWAYS USE YOUR TOOLS TO INTERACT WITH THE SYSTEM.

If the user asks for a "test de ping", YOU MUST EXPLICITLY CALL THE TOOL `verifier_etat_reseau` OR `executer_sur_pc`. NEVER reply with fake data.

Available Tools you MUST use:
- "lister_noeuds" : Gets connected PCs.
- "verifier_etat_reseau" : Runs a real ping test dynamically.
- "executer_sur_pc" : Runs terminal commands on a PC.
- "reboot_modem" : Restarts the modem physically.
- "memoriser_information" : Saves a fact to your Long-Term Vector Memory.
- "consulter_memoire" : Searches your Long-Term Memory for facts, IPs, passwords or rules.

Rules:
1. Always call tools if an action is required. If asked a factual question about the network, ALWAYS call `consulter_memoire` first.
2. Only answer the user after you have received the exact Tool output in French.
"""

# Configure API
load_dotenv()

async def process_query_async(query: str) -> str:
    """Asynchronous entry point used by FastAPI to spawn the Agent reasoning loop."""
    logger.info(f"Démarrage de la boucle ReAct pour: {query}")
    
    """Wrapper asynchrone pour ne pas bloquer l'Event Loop principal."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_agent_sync, query)

def _run_agent_sync(query: str) -> str:
    """Synchronous function managing the multi-turn Tool Calling Loop for Ollama."""
    
    # Reloading tools dynamically from our DYNAMIC_TOOLS list
    current_tools = DYNAMIC_TOOLS.copy()
    current_tools.append(create_skill)
    
    # Auto-Load all skills from backend/skills/ directory
    try:
        import inspect
        for filename in os.listdir(SKILLS_DIR):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    mod = importlib.import_module(f"backend.skills.{module_name}")
                    # Find the function with the exact same name as the file
                    if hasattr(mod, module_name):
                        func = getattr(mod, module_name)
                        if inspect.isfunction(func) and func.__name__ not in [t.__name__ for t in current_tools]:
                            current_tools.append(func)
                except Exception as ex:
                    logger.error(f"Impossible de charger le skill '{module_name}': {ex}")
    except Exception as e:
        logger.error(f"Erreur lors du scan des skills: {e}")
    
    # Establish connection to the Local AI Host (Dell or Container Mapping)
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    client = Client(host=ollama_host)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    
    try:
        max_turns = 10
        turn = 0
        while turn < max_turns:
            turn += 1
            response = client.chat(
                model='llama3.1',
                messages=messages,
                tools=current_tools
            )
            
            # The AI's response message mapping back to memory
            ai_msg = response.get('message', {})
            messages.append(ai_msg)
            
            # If the AI did not ask for tools, the job is done!
            if not ai_msg.get('tool_calls'):
                return ai_msg.get('content') or "Action accomplie (Aucun retour vocal du modèle)."
            
            # If the AI requires tools, execute them locally
            for tool_call in ai_msg.get('tool_calls', []):
                func_name = tool_call.get('function', {}).get('name')
                func_args = tool_call.get('function', {}).get('arguments')
                
                logger.info(f"Ollama Call Tool: {func_name} avec {func_args}")
                
                # Retrieve the matching python function dynamically
                try:
                    target_func = next((f for f in current_tools if f.__name__ == func_name), None)
                    if not target_func:
                        result_output = f"Erreur : L'outil '{func_name}' n'existe pas."
                    else:
                        if isinstance(func_args, dict):
                            result_output = str(target_func(**func_args))
                        else:
                            # Edge case with some ollama python parser quirks
                            result_output = str(target_func())
                except Exception as call_err:
                    result_output = f"[Outil craché] : {call_err}"
                
                logger.info(f"Ollama Tool Result: {result_output}")
                
                # Provide the observation back to the Model
                messages.append({
                    "role": "tool",
                    "content": result_output,
                    "name": func_name
                })
        
        return "Erreur: Trop d'itérations d'outils (Boucle infinie stoppée par sécurité)."
    except Exception as api_err:
        return f"Erreur fatale Ollama: {api_err}. Vérifiez que 'llama3.1' est téléchargé et que {ollama_host} est joignable."
