import requests
import sys

SERVER_URL = "http://100.80.201.113:8001/agent_task"

def main():
    print("==================================================")
    print("              INTERFACE AKA-ONE NOC               ")
    print("            (Connecté au Cerveau Ubuntu)          ")
    print("==================================================")
    print("Tapez 'quitter' pour fermer ce terminal.\n")
    
    while True:
        try:
            query = input("\n[Vous] > ")
            if query.strip().lower() in ['quitter', 'exit', 'quit']:
                break
            if not query.strip():
                continue
                
            print("[\u23F3 AKA-ONE réfléchit et exécute...]")
            
            response = requests.post(SERVER_URL, json={"query": query}, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n[AKA-ONE] >\n{data.get('response', 'Reponse vide.')}\n")
            else:
                print(f"\n[ERREUR SERVEUR] > Code {response.status_code}: {response.text}\n")
                
        except requests.exceptions.ConnectionError:
            print(f"\n[ERREUR] Impossible de joindre le Cerveau à {SERVER_URL}.")
            print("Vérifiez que le serveur Ubuntu tourne et que Tailscale est actif.\n")
        except Exception as e:
            print(f"\n[ERREUR CRITIQUE] > {e}\n")

if __name__ == "__main__":
    main()
