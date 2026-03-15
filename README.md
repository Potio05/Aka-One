# AKA-ONE 💻🎓
**Advanced Knowledge Assistant - One**  
*The Ultimate CS Tutor & Classroom Assistant*

AKA-ONE is an agentic AI platform designed to assist Computer Science students. It combines **RAG (Retrieval-Augmented Generation)** for answering course-specific questions, a **C-Visualizer** for debugging memory concepts, and **Google Classroom Integration** for autonomous learning.

![AKA-ONE Banner](https://img.shields.io/badge/Status-Online-brightgreen) ![Tech](https://img.shields.io/badge/Stack-FastAPI%20|%20Streamlit%20|%20Qdrant-blue)

---

## 🚀 Key Features

### 1. 💬 Terminal Chat (RAG + Chill Mode)
- **Contextual Answers**: Uses vector search (Qdrant) to answer questions based on your specific course materials.
- **Smart Fallback**: If the answer isn't in your PDFs, it switches to a general "CS Tutor" persona to keep the conversation going.
- **Persona**: "Khouya Taleb" - A friendly, Darija-speaking senior student who explains complex concepts simply.

### 2. 🧠 Memory Visualizer (C-Debugger)
- **Interactive Graph**: Visualizes the **Stack** and **Heap** memory layouts for C code snippets.
- **Pointer Tracking**: Automatically draws arrows between pointers and their targets.
- **Use Case**: Perfect for understanding `malloc`, pointers, and memory leaks.

### 3. 🍎 Google Classroom Sync (Auto-Ingestion)
- **One-Click Connect**: Authenticate securely via Google OAuth 2.0 directly in the UI.
- **Course Discovery**: Automatically lists your available Google Classroom courses.
- **Auto-Ingestion**: Downloads PDFs from the selected course and indexes them into the Vector Database in the background workers.

---

## 🛠️ Architecture

The system is built as a microservices architecture using Docker Compose:

| Service | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Streamlit (Python) | The "Neo-Glassmorphism" UI. Handles Auth flow and User Interaction. |
| **Backend** | FastAPI (Python) | API Gateway. Manages Auth, LLM orchestration (LlamaIndex), and Search. |
| **Worker** | Celery (Redis) | Background Task Queue. Handles long-running PDF downloads and Ingestion. |
| **Vector DB** | Qdrant | Stores embeddings of course materials for fast retrieval. |
| **LLM** | Ollama | Local Inference (Llama 3 / Mistral) running on the host or container. |

---

## 📦 Installation & Setup

### Prerequisites
- **Docker Desktop** installed and running.
- **Ollama** running locally (usually on port 11434).

### 1. Google Credentials (Target: `credentials.json`)
To enable Classroom features, you need a Google Cloud Project:
1.  Go to **Google Cloud Console**.
2.  Enable **Classroom API** and **Drive API**.
3.  Create **OAuth Desktop** (or Web) credentials.
4.  Download the JSON, rename it to `credentials.json`, and place it in the project root.
    *   *Note: If using Web credentials, ensure `http://localhost:8080/` is an authorized Redirect URI.*

### 2. Start the System
```bash
docker-compose up --build
```
*First run might take time to download Docker images and ML models.*

---

## 🎮 Usage Guide

### A. Accessing the Interface
Open your browser and navigate to:  
👉 **http://localhost:8501**

### B. Connecting Google Classroom
1.  Go to **Data Ingestion 📥** tab.
2.  If disconnected, click the **"Log in with Google"** button in the sidebar.
3.  Follow the Google popup to authorize access.
4.  Once green (**✅ Google Connected**), select a course from the dropdown and click **Ingest**.

### C. Visualizing Code
1.  Go to **Memory Visualizer 🧠** tab.
2.  Paste your C code (functions, pointers, etc.).
3.  Click **Execute Visualization**.
4.  See the generated Graphviz diagram of your Stack and Heap!

---

## 🔧 Troubleshooting

- **"Failed to generate login link"**:
    - Check if port `8080` is free (used for OAuth callback).
    - Ensure `credentials.json` is valid.
    - Restart backend: `docker restart talebuj_backend`.

- **"Empty Response" in Chat**:
    - The RAG might have found nothing. The system should fallback to general chat.
    - Check backend logs: `docker logs talebuj_backend`.

- **"System Offline"**:
    - Ensure Docker containers are running: `docker ps`.

---

**Built with ❤️ by AKA-ONE Team**  
*v2.0 - Premium Build*
