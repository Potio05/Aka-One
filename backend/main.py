from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from backend.celery_worker import ingest_classroom_course
from backend.services.ingestion import TalebRAG
from backend.services.visualizer import MemoryVisualizer
from backend.services.classroom import ClassroomService
import uuid

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TalebAI API")

# Models
class ChatRequest(BaseModel):
    query: str
    user_id: str = "default_user" # Added for Multi-Tenancy

class IngestRequest(BaseModel):
    course_id: str
    drive_folder_id: str
    user_id: str = "default_user" # Added for Multi-Tenancy

class VizRequest(BaseModel):
    code: str

# Services
rag_service = TalebRAG()
viz_service = MemoryVisualizer()
classroom_service = ClassroomService()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting TalebAI Backend...")
    # Initialize RAG connection (Qdrant check)
    try:
        rag_service.connect()
        logger.info("RAG Service Connected.")
    except Exception as e:
        logger.error(f"Failed to connect RAG Service: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.3.0"}

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Synchronous Chat Endpoint (direct to RAG)
    """
    try:
        response = rag_service.query(request.query, user_id=request.user_id)
        return {"answer": str(response)}
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Classroom Auth & Data Endpoints ---

@app.get("/api/auth/status")
def get_auth_status():
    return {"authenticated": classroom_service.is_authenticated()}

@app.get("/api/auth/login")
def login_google():
    try:
        url = classroom_service.start_auth_flow_thread()
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses")
def get_courses(q: str = None):
    try:
        courses = classroom_service.search_courses(q)
        return {"courses": courses}
    except Exception as e:
        return {"courses": [], "error": str(e)}

@app.post("/api/ingest")
async def ingest_course(request: IngestRequest, background_tasks: BackgroundTasks): # Modified endpoint signature
    """
    Trigger Background Ingestion via Celery
    """
    task_id = str(uuid.uuid4()) # Using uuid for task_id
    logger.info(f"Queuing ingestion for course {request.course_id} (Task {task_id}) User: {request.user_id}")
    
    # Send to Celery
    ingest_classroom_course.delay(request.course_id, request.drive_folder_id, request.user_id)
    
    return {"status": "queued", "task_id": task_id}

    return {"status": "queued", "task_id": task_id}

from fastapi import File, UploadFile
from backend.celery_worker import ingest_file_task
import shutil
import os

@app.post("/api/ingest/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = "default_user"):
    """
    Uploads a file and triggers ingestion.
    """
    task_id = str(uuid.uuid4())
    upload_dir = f"courses/uploads/{task_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"File uploaded to {file_path}. Queuing ingestion task {task_id}.")
        ingest_file_task.delay(upload_dir, user_id)
        
        return {"status": "queued", "task_id": task_id, "filename": file.filename}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/visualize")
def visualize_code(request: VizRequest):
    """
    Generates Memory Layout JSON for C Code
    """
    try:
        data = viz_service.analyze_code(request.code)
        return data
    except Exception as e:
        logger.error(f"Viz Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
