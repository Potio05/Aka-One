from fastapi.testclient import TestClient
from backend.main import app
import os
import shutil

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_auth_endpoints():
    response = client.get("/api/auth/status")
    # Even if False, it should return 200
    assert response.status_code == 200
    assert "authenticated" in response.json()

def test_upload_endpoint():
    # create dummy file
    with open("test.txt", "w") as f:
        f.write("This is a test document for RAG.")
    
    with open("test.txt", "rb") as f:
        response = client.post(
            "/api/ingest/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    
    # Clean up
    if os.path.exists("test.txt"):
        os.remove("test.txt")
