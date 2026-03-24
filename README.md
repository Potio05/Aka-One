<h1 align="center">AKA-ONE 2.0 : Sovereign Distributed AGI</h1>
<p align="center">
  <em>An autonomous, distributed, and self-hosted AI agent architecture built for Zero-Trust HomeLabs and NOCs.</em>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Llama_3.1-Local_Inference-blue" alt="Ollama">
  <img src="https://img.shields.io/badge/Memory-Qdrant_Vector_DB-orange" alt="Qdrant">
  <img src="https://img.shields.io/badge/Networking-Tailscale_Encrypted-green" alt="Tailscale">
</p>

## 🌌 Overview

**AKA-ONE 2.0** is an open-source, Sovereign framework that runs an autonomous ReAct AI agent distributed across an encrypted mesh network. It features self-healing network monitoring, long-term semantic memory, and dynamic skill injection.

Instead of relying on costly cloud providers, AKA-ONE leverages **Local LLMs (Ollama)** running on dedicated GPU hardware, communicating with a central Orchestrator through **Tailscale**.

## 🚀 Key Architectural Features

- **Distributed AI Processing**: The FastAPI orchestration server can run on a lightweight host (e.g., Ubuntu CPU server), routing inference jobs asynchronously to a heavy GPU node across the network via Tailscale port mapping.
- **RAG Long-Term Memory**: Eradicates the "goldfish memory" effect without costly Fine-Tuning. The AI generates contextual embeddings via `nomic-embed-text` and stores permanent network facts into a local **Qdrant Vector Database**.
- **Dynamic Skill Auto-Discovery**: AKA-ONE auto-loads any `*.py` scripts dropped into its `skills/` directory on boot. It inspects and masters new Python functions via reflection, treating them as new external tools.
- **Self-Healing NOC Watchdog**: Background process actively monitors network integrity (e.g., losing connection to 8.8.8.8) and can proactively trigger the AI agent to execute emergency actions (e.g., SSH into or use Playwright to reboot local routers) with zero human intervention.

## 🛠 Tech Stack

- **Orchestration**: `FastAPI`, `Uvicorn`, `Celery`.
- **Sovereign Intelligence**: `LlamaIndex`, `Ollama` (Llama 3.1 & nomic-embed).
- **Persistent Memory**: `Qdrant` (Vector database over TCP).
- **Physical Automation**: `Playwright` (Headless browser for IoT interactions).

## 📦 Usage & Deployment
*Copy the `.env.example` to `.env` and map `OLLAMA_HOST` to your dedicated local GPU node.*

```bash
sudo docker-compose up -d --build
```
> Attach the Interactive CLI: `python ask_aka.py`
