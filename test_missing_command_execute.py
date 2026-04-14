import sys
import os
from unittest.mock import patch

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import nomos

def mock_query(*args, **kwargs):
    if "relay" in args[0]:
        return {"message": {"content": '{"goal":"test", "constraints":[], "result":"ok", "uncertainty":"low", "next":"none", "command":""}'}}
    return {"message": {"content": "mock plan"}}

with patch('nomos.query_ollama', side_effect=mock_query):
    runtime = nomos.Runtime("/tmp/nomos-test", profile_name="read-only", execute=True)
    runtime.run_task("test missing command with execute")
