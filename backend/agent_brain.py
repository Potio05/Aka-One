import os
import sys
import asyncio
import importlib
import logging
import urllib.request
import json
import google.generativeai as genai
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
Tu es le cerveau autonome de "AKA-ONE", un Administrateur Système Distribué.
Tu as pour mission de gérer, d'analyser et de configurer des ordinateurs sur le réseau local.

Tu as des outils de base, mais surtout un outil SURPUISSANT : "create_skill(nom, code_python)".
Si on te demande une fonctionnalité complexe que tu n'as pas :
1. Tu utilises "create_skill" pour coder un outil Python autonome.
2. La fonction écrite DOIT avoir le nom "nom" et avoir une bonne docstring détaillée pour que tu saches comment l'utiliser ensuite.
3. Le skill est compilé et greffé à ton cerveau dynamiquement et automatiquement.

Exemple : Si on te demande de streamer l'écran, tu codes un skill "stream_screen" utilisant OpenCV ou autre.
Outils Standards:
- "lister_noeuds()" : Demande la liste des IDs (Noeuds).
- "verifier_etat_reseau()" : Obtient le ping et la connectivité vers la passerelle (192.168.100.1) et Google (8.8.8.8).
- "rechercher_logiciel(nom)" : Pour savoir comment s'appelle un logiciel ou obtenir de l'aide sur une syntaxe.
- "executer_sur_pc(id_pc, commande)" : Pour exécuter du bash ou Powershell sur les noeuds.

RÈGLES IMPORTANTES :
- Réfléchis toujours étape par étape (Thought -> Action -> Observation).
- Si tu dois installer quelque chose sur Windows, utilise "winget install <nom> --silent --accept-package-agreements --accept-source-agreements" (Phase 3.2).
- Si on te demande d'effectuer une action, utilise directement "executer_sur_pc" pour accomplir ta tâche, puis analyse le résultat.
- Fournis une réponse claire incluant un résumé des actions effectuées à l'utilisateur.
"""

# Configure API
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY manquant dans .env !")

async def process_query_async(query: str) -> str:
    """Asynchronous entry point used by FastAPI to spawn the Agent reasoning loop."""
    if not api_key:
        return "Erreur: La clé GEMINI_API_KEY n'est pas configurée dans .env"
        
    logger.info(f"Démarrage de la boucle ReAct pour: {query}")
    
    # Run the blocking Gemini inference in a thread to not freeze the async web requests
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, _run_agent_sync, query)
    return response

def _run_agent_sync(query: str) -> str:
    """Synchronous function where the google-generativeai client manages the Tool Loop."""
    
    # Reloading tools dynamically from our DYNAMIC_TOOLS list
    current_tools = DYNAMIC_TOOLS.copy()
    current_tools.append(create_skill)
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro',
        tools=current_tools,
        system_instruction=SYSTEM_PROMPT
    )
    
    try:
        # start_chat automatically manages the history and function calls
        # with enable_automatic_function_calling=True, the SDK handles the loop internally.
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        response = chat.send_message(query)
        logger.info(f"Observation finale: {response.text}")
        
        return response.text
        
    except Exception as e:
        logger.error(f"Erreur Agent: {e}")
        return f"Erreur de l'agent: {e}"
