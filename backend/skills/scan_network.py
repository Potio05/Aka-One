import platform
import subprocess
import logging

logger = logging.getLogger("scan_network")

def scan_network(ip_base: str = "192.168.100") -> str:
    """
    Outil d'Administration : Scanne le réseau local pour trouver les appareils actifs (via ARP ou ping).
    Fournir la base IP, par défaut "192.168.100".
    """
    logger.info(f"Scan réseau en cours sur {ip_base}.x ...")
    os_type = platform.system().lower()
    
    resultats = []
    
    try:
        if "windows" in os_type:
            # Exécute un arp -a pour voir le cache ARP local avec un peu de chance
            output = subprocess.check_output(["arp", "-a"], universal_newlines=True)
            for line in output.split('\n'):
                if ip_base in line and "dynamique" in line.lower() or "dynamic" in line.lower():
                    resultats.append(line.strip())
        else:
            # Sur linux, on peut utiliser arp -a aussi
            output = subprocess.check_output(["arp", "-a"], universal_newlines=True)
            for line in output.split('\n'):
                if ip_base in line:
                    resultats.append(line.strip())
                    
        if not resultats:
            return f"Le scan ARP n'a pas trouvé de nouveaux appareils dynamiques correspondants à {ip_base}.x. Note: L'hôte qui lance cette commande doit avoir interagi avec eux récemment pour qu'ils soient dans le cache."
            
        return "Appareils trouvés sur le réseau local :\n" + "\n".join(resultats)
    except Exception as e:
        return f"Erreur lors du scan réseau : {e}"
