import pytest
from unittest.mock import patch
import nomos
import json
import os

def test_missing_keys_blocks_execution(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Mock relay response with missing required keys
    def mock_query(*args, **kwargs):
        if "relay" in args[0]:
            return {"message": {"content": '{"goal":"test", "command":"ls"}'}}
        return {"message": {"content": "mock plan"}}

    with patch('nomos.query_ollama', side_effect=mock_query):
        runtime = nomos.Runtime(str(workspace), profile_name="read-only")
        # run_task prints BLOCKED to stderr/stdout
        runtime.run_task("test missing keys")
        
        # Check journal for blocked status
        journal_path = workspace / ".nomos" / "journal.log"
        with open(journal_path, "r") as f:
            content = f.read()
            assert "BLOCKED: Malformed relay protocol" in content

def test_typed_malformed_blocks_execution(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Mock relay response with incorrect type for constraints (string instead of list)
    def mock_query(*args, **kwargs):
        if "relay" in args[0]:
            return {"message": {"content": '{"goal":"test", "constraints":"not-a-list", "result":"ok", "uncertainty":"none", "next":"none", "command":"ls"}'}}
        return {"message": {"content": "mock plan"}}

    with patch('nomos.query_ollama', side_effect=mock_query):
        runtime = nomos.Runtime(str(workspace), profile_name="read-only")
        runtime.run_task("test mistyped relay")
        
        journal_path = workspace / ".nomos" / "journal.log"
        with open(journal_path, "r") as f:
            content = f.read()
            assert "Incorrect type for 'constraints'" in content
