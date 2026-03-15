import os
import sys
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import qdrant_client

def main():
    print("--- TalebAI Phase 1: Local RAG (Preuve de Concept) ---")
    
    # 1. Setup Configuration
    print("[*] Configuring Local LLM (Ollama) & Embeddings...")
    
    # USE A LOCAL EMBEDDING MODEL (Offline friendly)
    # BAAI/bge-m3 is excellent for Multilingual (Arabic/French/English)
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-m3" 
    )
    
    # USE OLLAMA (Make sure 'ollama serve' is running and 'llama3' is pulled)
    # You can change model="gemma2" or "mistral" depending on what you have.
    Settings.llm = Ollama(model="llama3", request_timeout=120.0)

    # 2. Setup Vector Database (Qdrant)
    print("[*] Connecting to Qdrant (localhost:6333)...")
    client = qdrant_client.QdrantClient(url="http://localhost:6333")
    vector_store = QdrantVectorStore(client=client, collection_name="taleb_courses")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 3. Ingestion
    courses_dir = "./courses"
    if not os.path.exists(courses_dir):
        os.makedirs(courses_dir)
        print(f"[!] Created directory {courses_dir}. Please put PDF files there!")
        return

    files = os.listdir(courses_dir)
    if not files:
        print(f"[!] No files found in {courses_dir}. Please add some PDFs/Slides.")
        return

    print(f"[*] Loading documents from {courses_dir}...")
    documents = SimpleDirectoryReader(courses_dir).load_data()
    
    print("[*] Indexing/Vectorizing docs (This might take a moment)...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    print("[*] Indexing Complete!")

    # 4. Load Persona
    prompt_path = "prompts/darija_persona.md"
    system_prompt = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
        print("[*] Loaded 'Chrahli b Darja' Persona.")
    else:
        print(f"[!] Warning: Persona file not found at {prompt_path}")

    # 5. Query Loop
    print("\n--- TalebAI is Ready (Type 'exit' to quit) ---")
    
    # Apply system prompt to the query engine
    query_engine = index.as_query_engine(
        streaming=True,
        similarity_top_k=3,
        system_prompt=system_prompt 
    )

    while True:
        try:
            user_input = input("\n(TalebAI) Entree ta question: ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            print("...")
            streaming_response = query_engine.query(user_input)
            streaming_response.print_response_stream()
            print("\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    main()
