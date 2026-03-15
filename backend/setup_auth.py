import os
import logging
# Allow OAuth over Http for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Relax scope check because Google might return different scopes (order/extra)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
          'https://www.googleapis.com/auth/drive.readonly']

def setup():
    # REMARQUE : Assurez-vous d'avoir rempli 'credentials.json' avec vos propres clés API Google
    # obtenues via la Google Cloud Console (APIs & Services -> Credentials).
    creds_path = "credentials.json"
    
    # REMARQUE : 'token.json' sera généré automatiquement par ce script après votre connexion réussie via le navigateur.
    # Ne le remplissez pas manuellement.
    token_path = "token.json"
    
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found.")
        print("Veuillez créer et configurer 'credentials.json' avec vos clés API Google.")
        return

    print("--- Google Auth Setup ---")
    print("1. Launching local server for auth...")
    print("2. You will be asked to visit a URL.")
    print("3. IMPORTANT: If using 'Web App' creds, ensure 'http://localhost:8080/' is added to Redirect URIs in Google Cloud Console.")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        # Use port 8080 which we will map in docker-compose
        # Force 'consent' to ensure we get a refresh_token
        creds = flow.run_local_server(port=8080, open_browser=False, bind_addr="0.0.0.0", prompt='consent')
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
        print(f"\n[SUCCESS] Auth complete! '{token_path}' created.")
        print("You can now restart the worker: docker restart talebuj_worker")
        
    except Exception as e:
        print(f"\n[ERROR] Auth failed: {e}")
        print("Tip: Check if 'http://localhost:8080/' is in your Authorized Redirect URIs.")

if __name__ == "__main__":
    setup()
