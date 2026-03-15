from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

class TalebRAG:
    def __init__(self):
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = None
        self.index = None
        # We remove self.query_engine caching because it needs to be per-user now
        
        # Initialize Settings (Global)
        # Switching to smaller model for faster dev/debugging
        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        Settings.llm = Ollama(model="llama3", base_url=self.ollama_host, request_timeout=120.0)

    def connect(self):
        """Connects to Qdrant and loads the Index."""
        print(f"[*] Connecting to Qdrant at {self.qdrant_host}...")
        self.client = qdrant_client.QdrantClient(url=f"http://{self.qdrant_host}:6333")
        
        # Ensure collection exists
        if not self.client.collection_exists("taleb_courses_small"):
            print("[*] Creating new collection: taleb_courses_small")
            from qdrant_client.http import models
            self.client.create_collection(
                collection_name="taleb_courses_small",
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

        vector_store = QdrantVectorStore(client=self.client, collection_name="taleb_courses_small")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Load index from existing vector store (no re-ingestion by default)
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=storage_context
            )
            print("[*] Index Loaded.")
        except Exception as e:
            print(f"[!] Warning: Could not load index (might be empty): {e}")
            self.index = VectorStoreIndex.from_documents(
                [], storage_context=storage_context
            )

    def query(self, question: str, user_id: str = "default_user"):
        """Queries the RAG pipeline with User Isolation."""
        if not self.index:
            self.connect()
            
        # Define filters for Multi-Tenancy
        filters = MetadataFilters(
            filters=[
                ExactMatchFilter(key="user_id", value=user_id)
            ]
        )
        
        # Load Persona
        system_prompt = "You are AKA-ONE, a helpful CS tutor provided answer in a mix of Algerian Darija and French/English technical terms."
        try:
            with open("prompts/darija_persona.md", "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            pass
        
        # Instantiate PER-REQUEST Engine with Filters
        chat_engine = self.index.as_chat_engine(
            chat_mode="condense_plus_context",
            similarity_top_k=3,
            system_prompt=system_prompt,
            verbose=True,
            filters=filters 
        )
            
        print(f"[*] Querying (User: {user_id}): {question}")
        response = chat_engine.chat(question)
        print(f"[*] Raw Response: {response}")
        
        # Fallback for "Chit-Chat" if RAG fails (Empty Response)
        if str(response).strip() == "Empty Response":
            print("[!] RAG returned Empty Response. Falling back to direct LLM chat...")
            # Use the underlying LLM directly
            from llama_index.core.llms import ChatMessage
            messages = [
                ChatMessage(role="system", content="You are AKA-ONE, a helpful AI tutor. The user is asking a general question (not in the course material). Answer kindly in Darija."),
                ChatMessage(role="user", content=question)
            ]
            direct_response = Settings.llm.chat(messages)
            return direct_response
            
        return response

    def ingest(self, directory_path: str, user_id: str = "default_user"):
        """Ingests documents from a directory, tagged with user_id."""
        if not self.index:
            self.connect()
            
        documents = SimpleDirectoryReader(directory_path).load_data()
        
        # Tag documents with User ID for Multi-Tenancy
        for doc in documents:
            doc.metadata["user_id"] = user_id
            
        # Update the index
        self.index.insert_nodes(self.index.as_retriever().node_parser.get_nodes_from_documents(documents)) 
        # Easier: just use insert. But insert relies on doc store.
        # Let's use the standard flow but with metadata.
        
        for doc in documents:
            self.index.insert(doc)
            
        print(f"[*] Ingested {len(documents)} documents for user {user_id} from {directory_path}")
