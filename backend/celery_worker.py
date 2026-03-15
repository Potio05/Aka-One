import os
from celery import Celery
import time
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis Connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_URL = f"redis://{REDIS_HOST}:6379/0"

celery = Celery("taleb_worker", broker=REDIS_URL, backend=REDIS_URL)

@celery.task(bind=True)
def ingest_classroom_course(self, course_id: str, drive_folder_id: str):
    """
    Background Task: Ingests PDFs from Google Classroom.
    """
    logger.info(f"[Task {self.request.id}] Starting Ingestion for Course {course_id}...")
@celery.task
def ingest_classroom_course(course_id: str, drive_folder_id: str = None, user_id: str = "default_user"):
    """
    Background Task:
    1. Download PDF from Classroom/Drive
    2. Index into Qdrant (with user_id filter)
    """
    logger.info(f"Starting Ingestion for Course {course_id} (User: {user_id})...")
    
    # 1. Download
    download_dir = f"courses/{course_id}"
    os.makedirs(download_dir, exist_ok=True) # Ensure directory exists

    # 1. Fetch from Google Classroom
    from backend.services.classroom import ClassroomService
    classroom = ClassroomService()
    
    logger.info("Fetching materials from Classroom...")
    files = classroom.download_pdfs(course_id, download_dir)
    
    if not files:
        logger.warning("No files found (or Mock Mode).")
    else:
        logger.info(f"PDFs Ready: {files}. Indexing...")
        
    # 2. Ingest
    from backend.services.ingestion import TalebRAG
    rag = TalebRAG()
    try:
        if not rag.index: # Assuming rag.index is a property that indicates connection status
            rag.connect()
            
        rag.ingest(download_dir, user_id=user_id) # Pass user_id
        return f"Ingestion Complete for {course_id}"
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise e

@celery.task
def ingest_file_task(directory_path: str, user_id: str = "default_user"):
    """
    Background Task: Ingests uploaded files from a specific directory.
    """
    logger.info(f"Starting File Ingestion from {directory_path} (User: {user_id})...")
    
    from backend.services.ingestion import TalebRAG
    rag = TalebRAG()
    try:
        if not rag.index:
            rag.connect()
            
        rag.ingest(directory_path, user_id=user_id)
        return f"File Ingestion Complete from {directory_path}"
    except Exception as e:
        logger.error(f"File Ingestion failed: {e}")
        raise e
