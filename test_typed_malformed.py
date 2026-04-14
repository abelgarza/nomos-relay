import sys
import os
from unittest.mock import patch

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import nomos

def mock_query(*args, **kwargs):
    if "relay" in args[0]:
        # constraints should be array, but here it is a string
        return {"message": {"content": '{"goal":"test", "constraints":"not an array", "result":"ok", "uncertainty":"low", "next":"none", "command":"ls"}'}}
    return {"message": {"content": "mock plan"}}

with patch('nomos.query_ollama', side_effect=mock_query):
    runtime = nomos.Runtime("/tmp/nomos-test", profile_name="read-only")
    runtime.run_task("test mistyped relay")
