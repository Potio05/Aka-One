import os
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
          'https://www.googleapis.com/auth/drive.readonly']

class ClassroomService:
    def __init__(self, credentials_path="credentials.json"):
        self.creds = None
        # IMPORTANT : Le fichier pointé par credentials_path (ex: 'credentials.json') doit être rempli 
        # manuellement avec vos identifiants clients OAuth 2.0 de Google Cloud Console.
        self.credentials_path = credentials_path
        
        # Le fichier 'token.json' sera créé automatiquement après la première authentification réussie.
        self.token_path = "token.json"
        
    def authenticate(self):
        """Authenticates with Google API using credentials.json or existing token."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    return False
            else:
                if os.path.exists(self.credentials_path):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                        self.creds = flow.run_local_server(port=0)
                        # Save the credentials for the next run
                        with open(self.token_path, 'w') as token:
                            token.write(self.creds.to_json())
                    except Exception as e:
                        logger.error(f"Error during new auth flow: {e}")
                        return False
                else:
                    logger.warning(f"Credentials file {self.credentials_path} not found. Running in MOCK mode.")
                    return False
        return True

    def is_authenticated(self):
        """Checks if we have valid credentials."""
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                return creds.valid
            except:
                return False
        return False

    def list_courses(self):
        """Lists available courses."""
        if not self.authenticate():
            return [{"id": "mock_101", "name": "Mock CS Course (No Creds)"}]
            
        try:
            service = build('classroom', 'v1', credentials=self.creds)
            results = service.courses().list(pageSize=10).execute()
            courses = results.get('courses', [])
            return [{"id": c['id'], "name": c['name']} for c in courses]
        except Exception as e:
            logger.error(f"API Error listing courses: {e}")
            return []

    def search_courses(self, query: str):
        """Fuzzy searches courses by name."""
        all_courses = self.list_courses()
        if not query:
            return all_courses
        
        query = query.lower()
        return [c for c in all_courses if query in c['name'].lower()]

    def start_auth_flow_thread(self):
        """Starts a one-time local server in a thread to handle the OAuth callback."""
        import threading
        from wsgiref.simple_server import make_server
        import urllib.parse
        
        # Define settings
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
        flow.redirect_uri = "http://localhost:8080/"
        
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        
        def simple_app(environ, start_response):
            """Simple WSGI app to capture code."""
            query = environ.get('QUERY_STRING', '')
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                code = params['code'][0]
                try:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                    status = "200 OK"
                    body = b"Authentication Successful! You can close this window."
                except Exception as e:
                    status = "500 Internal Server Error"
                    body = f"Auth Failed: {e}".encode('utf-8')
            else:
                status = "400 Bad Request"
                body = b"No code found."

            start_response(status, [('Content-Type', 'text/plain')])
            return [body]

        def run_server():
            # Create a server that handles ONE request then dies (or stays up briefly)
            # For simplicity, we make it a daemon thread that stays up until it gets a token or we restart
            try:
                httpd = make_server('0.0.0.0', 8080, simple_app)
                logger.info("Auth Server listening on 8080...")
                httpd.handle_request() # Handle ONE request
                logger.info("Auth Server stopped.")
            except Exception as e:
                logger.error(f"Failed to start auth server: {e}")

        # Start the server in a thread
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        
        return auth_url

    def download_pdfs(self, course_id, download_dir):
        """Downloads PDFs from a specific course to the directory."""
        if not self.authenticate():
            logger.info("Mock Mode: Simulating download.")
            # Create a dummy PDF for verification
            dummy_path = os.path.join(download_dir, "mock_lecture.pdf")
            if not os.path.exists(dummy_path):
                with open(dummy_path, "w") as f:
                    f.write("This is a mock lecture content about Google Classroom integration.")
            return ["mock_lecture.pdf"]

        try:
            service = build('classroom', 'v1', credentials=self.creds)
            drive_service = build('drive', 'v3', credentials=self.creds)
            
            # List course work
            course_work = service.courses().courseWork().list(courseId=course_id).execute()
            downloaded_files = []
            
            if 'courseWork' in course_work:
                for work in course_work.get('courseWork', []):
                    # Check materials
                    if 'materials' in work:
                        for material in work['materials']:
                            if 'driveFile' in material:
                                drive_file = material['driveFile']['driveFile']
                                title = drive_file['title']
                                file_id = drive_file['id']
                                
                                if title.lower().endswith('.pdf'):
                                    logger.info(f"Found PDF: {title}")
                                    self._download_file(drive_service, file_id, title, download_dir)
                                    downloaded_files.append(title)
            return downloaded_files
        except Exception as e:
            logger.error(f"API Error downloading files: {e}")
            return []

    def _download_file(self, drive_service, file_id, file_name, destination_folder):
        request = drive_service.files().get_media(fileId=file_id)
        filepath = os.path.join(destination_folder, file_name)
        
        # Ensure dir exists
        os.makedirs(destination_folder, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        logger.info(f"Downloaded {file_name}")
