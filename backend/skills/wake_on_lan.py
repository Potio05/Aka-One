import socket
import logging

logger = logging.getLogger("wake_on_lan")

def wake_on_lan(mac_address: str) -> str:
    """
    Outil d'Administration : Envoie un Magic Packet (Wake-On-Lan) pour allumer un PC éteint sur le réseau local.
    Le mac_address doit être au format "AA:BB:CC:DD:EE:FF".
    """
    mac_address = mac_address.replace("-", ":").upper()
    
    if len(mac_address) != 17:
        return "Erreur: Le format de l'adresse MAC est invalide. Utilisez XX:XX:XX:XX:XX:XX."
        
    try:
        # Construction du Magic Packet
        mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        
        # Envoi en broadcast UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ("255.255.255.255", 9))
        sock.close()
        
        logger.info(f"Magic Packet envoyé à {mac_address}")
        return f"Succès: Le paquet de réveil Wake-On-Lan a été diffusé sur le réseau pour l'adresse MAC {mac_address}."
    except Exception as e:
        logger.error(f"Erreur WOL : {e}")
        return f"Échec de l'envoi du Wake-On-Lan : {e}"
