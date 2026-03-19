from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess
import logging
import os

# --- LOCAL NODE CLIENT (AKA-NODE) ---
# Runs on each physical PC in the network.
# Listens for commands from the Central Brain.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AKA-NODE Executor")

class CommandRequest(BaseModel):
    command: str

@app.post("/execute")
async def execute_command(req: CommandRequest):
    """
    WARNING: This executes arbitrary shell commands.
    In a real-world scenario, you MUST add authentication (API Keys/Tokens).
    """
    logger.warning(f"Executing command requested by Brain: {req.command}")
    try:
        # Run command securely
        # Using shell=True is required for complex pipes/windows commands, 
        # but again, extreme security risk.
        result = subprocess.run(
            req.command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=120 # Prevent hanging forever
        )
        
        return {
            "status": "success",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command execution timed out.")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/health")
def health_check():
    return {"status": "online", "machine": os.environ.get("COMPUTERNAME", "Unknown")}

if __name__ == "__main__":
    import uvicorn
    # In production, bind to 0.0.0.0 and secure the endpoint.
    uvicorn.run(app, host="0.0.0.0", port=8081)
