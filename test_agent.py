import requests

print("Envoi de la tâche au Cerveau...")
res = requests.post(
    "http://127.0.0.1:8000/agent_task",
    json={"query": "Utilise lister_noeuds pour trouver qui est connecté. Ensuite, exécute `ipconfig` sur le premier PC que tu trouves et donne-moi son adresse IPv4 locale."}
)
print("Réponse du Cerveau:", res.text)
