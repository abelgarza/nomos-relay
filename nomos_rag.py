import os
import json
import requests
import argparse
import lancedb
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Any

# --- Interfaces (Patrón Estrategia) ---

class EmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        pass

class VectorStoreProvider(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        pass

# --- Implementaciones ---

class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str = "nomic-embed-text", url: str = "http://localhost:11434/api/embeddings"):
        self.model = model
        self.url = url

    def get_embedding(self, text: str) -> List[float]:
        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "prompt": text
            })
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

class LanceDBProvider(VectorStoreProvider):
    def __init__(self, db_path: str, table_name: str = "workspace_code"):
        self.db = lancedb.connect(db_path)
        self.table_name = table_name

    def add_documents(self, documents: List[Dict[str, Any]]):
        if not documents:
            return
        
        df = pd.DataFrame(documents)
        # We use mode="overwrite" to ensure a clean re-index and avoid duplicates
        # This aligns with the "Nomos" philosophy of deterministic state.
        self.db.create_table(self.table_name, data=df, mode="overwrite")

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if self.table_name not in self.db.list_tables():
            return []
        
        table = self.db.open_table(self.table_name)
        results = table.search(query_vector).limit(top_k).to_pandas()
        return results.to_dict('records')

# --- Manager y Utilidades de Indexación ---

class RAGManager:
    def __init__(self, workspace_path: str, embedding_provider: EmbeddingProvider, vector_store: VectorStoreProvider):
        self.workspace_path = workspace_path
        self.embedder = embedding_provider
        self.store = vector_store

    def index_workspace(self, extensions=(".py", ".js", ".json", ".md", ".sh")):
        documents = []
        for root, _, files in os.walk(self.workspace_path):
            if ".git" in root or ".nomos" in root or "__pycache__" in root:
                continue
            
            for file in files:
                if file.endswith(extensions):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if not content.strip():
                                continue
                            
                            # Improved chunking by lines with overlap
                            lines = content.split('\n')
                            chunks = []
                            chunk_size = 50  # lines
                            overlap = 10
                            
                            for i in range(0, len(lines), chunk_size - overlap):
                                chunk_lines = lines[i:i + chunk_size]
                                chunk_text = '\n'.join(chunk_lines)
                                if len(chunk_text.strip()) > 10:
                                    chunks.append(chunk_text)
                            
                            for i, chunk in enumerate(chunks):
                                print(f"Indexing {file} [chunk {i}]...")
                                vector = self.embedder.get_embedding(chunk)
                                if vector:
                                    documents.append({
                                        "vector": vector,
                                        "text": chunk,
                                        "metadata": json.dumps({
                                            "file": os.path.relpath(path, self.workspace_path),
                                            "chunk": i
                                        })
                                    })
                    except Exception as e:
                        print(f"Error reading {path}: {e}")
        
        if documents:
            self.store.add_documents(documents)
            print(f"Indexed {len(documents)} chunks.")

    def _normalize_query(self, text: str) -> str:
        """Translates the query to English using the local gemma4-nomos model if necessary."""
        try:
            # We use a very strict prompt to avoid conversational filler
            prompt = f"Translate the following technical query to English. If it is already in English, output it exactly as is. Output ONLY the translation, no quotes, no explanations, no filler:\n\n{text}"
            response = requests.post("http://localhost:11434/api/chat", json={
                "model": "gemma4-nomos",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0}
            }, timeout=10)
            response.raise_for_status()
            translated = response.json()["message"]["content"].strip()
            # If it's too long or empty, fallback to original to be safe
            if translated and len(translated) < len(text) * 4:
                return translated
        except Exception:
            # Silent fallback to original text if translation fails
            pass
        return text

    def query(self, text: str, top_k: int = 3) -> str:
        normalized_text = self._normalize_query(text)
        vector = self.embedder.get_embedding(normalized_text)
        if not vector:
            return ""
        
        results = self.store.search(vector, top_k=top_k)
        context = "\n---\n".join([f"Source: {json.loads(r['metadata'])['file']}\nContent:\n{r['text']}" for r in results])
        return context

# --- CLI de RAG ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nomos RAG Engine")
    parser.add_argument("--workspace", default=os.getcwd(), help="Workspace path")
    parser.add_argument("--index", action="store_true", help="Index the workspace")
    parser.add_argument("--query", help="Query the RAG store")
    parser.add_argument("--top_k", type=int, default=3, help="Top K results")
    
    args = parser.parse_args()
    
    workspace = os.path.abspath(args.workspace)
    db_path = os.path.join(workspace, ".nomos", "vector_store")
    os.makedirs(db_path, exist_ok=True)
    
    embedder = OllamaEmbeddingProvider()
    store = LanceDBProvider(db_path)
    manager = RAGManager(workspace, embedder, store)
    
    if args.index:
        manager.index_workspace()
    elif args.query:
        print(manager.query(args.query, top_k=args.top_k))
    else:
        parser.print_help()
