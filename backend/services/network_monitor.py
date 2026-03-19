import os
import platform
import subprocess
import time
import threading
import logging

logger = logging.getLogger("NetworkMonitor")

# Objet partagé Thread-Safe pour stocker les résultats et les rendre accessibles à FastAPI/Gemini
NETWORK_STATUS = {
    "192.168.100.1": {"status": "inconnu", "latency": "inconnu"},
    "8.8.8.8": {"status": "inconnu", "latency": "inconnu"},
    # On peut ajouter ici les IP Tailscale fixes si nécessaire
}

class NetworkMonitor:
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.targets = list(NETWORK_STATUS.keys())
        self.running = False
        self._thread = None
        self.os_type = platform.system().lower()

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logger.info(f"NOC: Service de monitoring réseau démarré (intervalle: {self.interval}s)")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def _ping(self, host: str):
        # Détection de l'OS pour ajuster l'argument du ping
        param = "-n" if "windows" in self.os_type else "-c"
        command = ["ping", param, "1", host]
        
        try:
            # shell=True n'est pas nécessaire et évite certains problèmes de sécurité si on passe une IP
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True, timeout=5)
            # Analyse très basique pour deviner la latence
            latency = "ok"
            for line in output.split('\n'):
                if "temps=" in line or "time=" in line:
                    parts = line.split(" ")
                    for p in parts:
                        if p.startswith("temps=") or p.startswith("time="):
                            latency = p.split("=")[1]
                            break
            return True, latency
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
             return False, "timeout / hors ligne"
        except Exception as e:
            return False, str(e)

    def _monitor_loop(self):
        while self.running:
            for target in self.targets:
                logger.debug(f"Ping {target}...")
                is_up, latency = self._ping(target)
                NETWORK_STATUS[target] = {
                    "status": "en ligne" if is_up else "hors ligne",
                    "latency": latency,
                    "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            time.sleep(self.interval)

# Instance singleton à importer ailleurs
monitor = NetworkMonitor(interval=60)
