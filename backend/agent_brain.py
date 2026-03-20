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
    """Outil 0 : Retourne la liste des IDs des PCs (Noeuds) actuellement connectés au réseau."""
    if not WS_MANAGER:
        return "Erreur: WS_MANAGER non initialisé."
    nodes = list(WS_MANAGER.active_connections.keys())
    if not nodes:
        return "Aucun PC n'est connecté actuellement."
    return f"PCs connectés : {', '.join(nodes)}"

def verifier_etat_reseau() -> str:
    """Outil de surveillance : Retourne l'état de latence actuel du routeur local et de l'accès internet."""
    from backend.services.network_monitor import NETWORK_STATUS
    res = "Statut Réseau (NOC) :\n"
    for target, info in NETWORK_STATUS.items():
        res += f"- {target} : {info['status']} (Latence: {info['latency']}, Dernier check: {info.get('last_checked', 'N/A')})\n"
    return res

def rechercher_logiciel(nom: str) -> str:
    """
    Outil 1 : Utilise une recherche pour trouver un logiciel ou des commandes d'administration.
    This simulates a quick web search or a package checking tool.
    """
    logger.info(f"Outil appelé: rechercher_logiciel({nom})")
    # Simulation d'un faux outil ou appel REST simple
    # You can expand this to true Google Search if needed.
    return f"Résultat: '{nom}' (Il est conseillé d'utiliser le gestionnaire de paquet système standard. Sur Windows: 'winget install {nom}', Sur Linux: 'apt-get install {nom}')."

def executer_sur_pc(id_pc: str, commande: str) -> str:
    """
    Outil 2 : Envoie une commande terminal à exécuter sur un PC spécifique via WebSocket, et renvoie le stdout/stderr.
    """
    if not WS_MANAGER or not SERVER_LOOP:
        return "[Erreur] Serveur WebSocket non initialisé."
        
    logger.info(f"Outil appelé: executer_sur_pc({id_pc}, '{commande}')")
    
    # We must bridge sync tool execution with the async WebSocket Server
    # We schedule the coroutine in the main loop and wait for it.
    future = asyncio.run_coroutine_threadsafe(
        WS_MANAGER.send_and_wait(id_pc, commande),
        SERVER_LOOP
    )
    
    try:
        # Wait up to 60s for the remote PC to execute and respond
        result = future.result(timeout=60)
        # Formater la réponse pour Gemini
        status = result.get("status")
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        return f"Status: {status}\nStdout: {stdout}\nStderr: {stderr}"
    except Exception as e:
        return f"[Erreur lors de l'exécution]: {e}"

# --- ARCHITECTURE DES PLUGINS (Phase 4) ---

# Liste globale dynamique des outils de l'agent
DYNAMIC_TOOLS = [lister_noeuds, verifier_etat_reseau, rechercher_logiciel, executer_sur_pc]

def create_skill(nom: str, code_python: str) -> str:
    """
    Outil 4 : Permet à l'IA de s'auto-améliorer en écrivant un nouveau code Python (un 'skill')
    qui sera chargé dynamiquement en mémoire comme un nouvel outil.
    LE CODE PYTHON DOIT CONTENIR: une fonction portant EXACTEMENT le même nom que l'argument `nom`.
    """
    filepath = os.path.join(SKILLS_DIR, f"{nom}.py")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_python)
            
        # Chargement dynamique
        module_name = f"backend.skills.{nom}"
        
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
            action_desc = "rechargé"
        else:
            module = importlib.import_module(module_name)
            action_desc = "importé"
            
        # On suppose que le code python contient une fonction portant le même nom
        if hasattr(module, nom):
            func = getattr(module, nom)
            # Ajout à la liste des outils si elle n'y est pas encore
            if func.__name__ not in [t.__name__ for t in DYNAMIC_TOOLS]:
                DYNAMIC_TOOLS.append(func)
            return f"Succès: Le skill '{nom}' a été {action_desc} et ajouté dynamiquement aux outils du Cerveau ! Tu peux l'utiliser lors de ta prochaine action."
        else:
            return f"Erreur: Le fichier {nom}.py a été créé, mais il ne contient pas de fonction '{nom}'."
    except Exception as e:
        return f"Erreur critique lors de la création du skill: {e}"

# --- SYSTEM PROMPT & AGENT LOOP ---

SYSTEM_PROMPT = """
Tu es l'Administrateur Système (NOC) en chef de l'infrastructure AKA-ONE.
TU AS TOUS LES DROITS D'ACCÈS DU CRÉATEUR.
NE RÉPONDS JAMAIS QUE TU ES UNE SIMPLE IA DÉPOURVUE D'ACCÈS. 
Au lieu de parler, tu DOIS TOUJOURS utiliser tes Outils (Function Calling) pour agir.

Tu as 4 Outils Standards OBLIGATOIRES:
1. "lister_noeuds()" : Cherche les PCs en ligne.
2. "verifier_etat_reseau()" : Donne le ping réseau (vers 8.8.8.8 et 192.168.100.1). OBLIGATOIRE qiuand on te demande de tester ou faire un ping global.
3. "executer_sur_pc(id_pc, commande)" : Si on te demande de faire un diagnostic spécifique (ex: ipconfig, ping), trouve l'ID d'un pc via lister_noeuds() puis utilise cet outil pour lancer la commande bash/powershell.
4. "reboot_modem()" : LANCE CET OUTIL SANS HÉSITER si on te demande formellement de redémarrer le modem ou internet.

RÈGLE D'OR : N'invente pas les résultats. Invoque la fonction, attends de recevoir le retour, puis dis ce que la fonction a retourné de manière robotique et brève.
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
    
    # Try loading reboot_modem if it exists
    try:
        from backend.skills.reboot_modem import reboot_modem
        if reboot_modem.__name__ not in [t.__name__ for t in current_tools]:
            current_tools.append(reboot_modem)
    except Exception:
        pass
    
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
