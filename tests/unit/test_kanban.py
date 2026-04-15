import pytest
import os
import json
from nomos_relay.nomos_kanban import NomosKanban

def test_kanban_initialization(tmp_path):
    db_path = str(tmp_path)
    kanban = NomosKanban(db_path, "test_kanban.json")
    
    tasks = ["Setup project", "Write code", "Test"]
    kanban.init_board("Test Objective", tasks)
    
    board = kanban.get_full_board()
    assert len(board) == 3
    assert board[0]["description"] == "Setup project"
    assert board[0]["state"] == "todo"
    assert board[0]["objective"] == "Test Objective"

def test_kanban_lifecycle(tmp_path):
    db_path = str(tmp_path)
    kanban = NomosKanban(db_path, "lifecycle.json")
    
    kanban.init_board("Lifecycle", ["Task A", "Task B"])
    
    # 1. Fetch first task
    task1 = kanban.get_next_task()
    assert task1 is not None
    assert task1["description"] == "Task A"
    assert task1["state"] == "doing"
    
    # 2. Check board state (task 1 should be doing)
    board = kanban.get_full_board()
    assert board[0]["state"] == "doing"
    assert board[1]["state"] == "todo"
    
    # 3. Mark task 1 as done
    kanban.update_task_state(task1["id"], "done", "Success", increment_attempts=True)
    board = kanban.get_full_board()
    assert board[0]["state"] == "done"
    assert board[0]["attempts"] == 1
    
    # 4. Fetch next task
    task2 = kanban.get_next_task()
    assert task2 is not None
    assert task2["description"] == "Task B"
    assert task2["state"] == "doing"
    
    # 5. Is complete? (Should be false)
    assert not kanban.is_complete()
    
    # 6. Finish Task 2
    kanban.update_task_state(task2["id"], "done")
    
    # 7. Should be complete
    assert kanban.is_complete()
    
    # 8. Next task should be None
    assert kanban.get_next_task() is None
