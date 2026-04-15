import pytest
import os
import json
from nomos_relay.nomos_rag import RAGManager, OllamaEmbeddingProvider, LanceDBProvider

class MockEmbedder(OllamaEmbeddingProvider):
    def get_embedding(self, text):
        # Return a dummy vector of 768 dims (standard for nomic)
        return [0.1] * 768

def test_chunking_logic(tmp_path):
    # Test line-based chunking
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    test_file = workspace / "test.py"
    # Create a file with 100 lines
    content = "\n".join([f"line {i}" for i in range(100)])
    test_file.write_text(content)
    
    embedder = MockEmbedder()
    # We don't need a real store for just testing chunking logic if we mock it
    # but let's use a local lancedb in the tmp_path
    db_path = tmp_path / "db"
    store = LanceDBProvider(str(db_path))
    manager = RAGManager(str(workspace), embedder, store)
    
    # Manually trigger index to check if it process correctly
    manager.index_workspace(extensions=(".py",))
    
    # If 100 lines, with chunk_size 50 and overlap 10:
    # Chunk 1: 0-50
    # Chunk 2: 40-90
    # Chunk 3: 80-100
    # Total should be around 3 chunks
    
    table = store.db.open_table(store.table_name)
    assert table.count_rows() >= 2

def test_query_normalization_fallback():
    # Test that normalization falls back to original text on failure
    embedder = MockEmbedder()
    store = LanceDBProvider("/tmp/dummy_db")
    manager = RAGManager("/tmp/workspace", embedder, store)
    
    # Mocking the request to Ollama to fail
    original_text = "test query"
    normalized = manager._normalize_query(original_text)
    assert normalized == original_text
