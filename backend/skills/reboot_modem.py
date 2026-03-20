import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger("reboot_modem")

def reboot_modem() -> str:
    """
    Outil personnalisé : Redémarre physiquement (soft reboot) le modem Huawei HG8145V5.
    Utilise Playwright (navigateur web invisible) pour contourner le cryptage Javascript de la page de login Huawei.
    """
    ROUTER_URL = "http://192.168.100.1"
    
    # --- IMPORTANT : MODIFIEZ CES IDENTIFIANTS SELON CEUX SOUS VOTRE MODEM ---
    USERNAME = "root"      # Typiquement 'root' ou 'telecomadmin' ou 'admin'
    PASSWORD = "admin"     # Typiquement 'admin' ou 'admintelecom'
    
    logger.info(f"Tentative de connexion au routeur Huawei {ROUTER_URL} via Playwright...")
    
    try:
        with sync_playwright() as p:
            # Lance un navigateur Chrome Chromium invisible
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Page de Connexion
            page.goto(ROUTER_URL)
            page.wait_for_timeout(1000) # Laisse le temps au JS de Huawei de charger
            
            # Les IDs standards de la page de login Huawei HG8145V5
            page.fill("#txt_Username", USERNAME)
            page.fill("#txt_Password", PASSWORD)
            page.click("#button_login")
            
            logger.info("Identifiants entrés. Attente de la validation...")
            page.wait_for_timeout(3000)
            
            # 2. Page de Reboot
            # L'URL directe de la frame de reboot chez Huawei
            reboot_page_url = f"{ROUTER_URL}/html/ssmp/reset/reset.asp"
            page.goto(reboot_page_url)
            page.wait_for_timeout(2000)
            
            # Script personnalisé pour intercepter la popup "Are you sure?"
            page.on("dialog", lambda dialog: dialog.accept())
            
            # Clique sur le bouton Redémarrer (l'ID du bouton sur le HG8145V5 est souvent 'btn_reboot')
            # On utilise un test au cas ou son ID est différent (Huawei utilise parfois 'Reset' ou des IDs en majuscule)
            try:
                page.click("#btn_reboot", timeout=2000)
            except:
                # Si l'ID a changé, on cible le bouton qui contient le texte Reboot/Restart/Redémarrer
                page.locator("button:has-text('Reboot'), button:has-text('Restart'), button:has-text('Redémarrer')").click()
                
            logger.info("Bouton de Redémarrage cliqué avec succès.")
            page.wait_for_timeout(2000) # Délai pour que le modem accuse réception
            
            browser.close()
            return f"Succès : Le modem Huawei HG8145V5 ({ROUTER_URL}) est en cours de redémarrage (l'Action Playwright a réussi)."
            
    except Exception as e:
        logger.error(f"Erreur Playwright lors du reboot: {e}")
        return f"Échec du redémarrage du modem Huawei : {str(e)}"
