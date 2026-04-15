import json
import os
import sys
from typing import List, Dict, Any, Optional

class NomosKanban:
    def __init__(self, db_path: str, file_name: str = "kanban.json"):
        self.path = os.path.join(db_path, file_name)
        os.makedirs(db_path, exist_ok=True)

    def _save(self, data: List[Dict[str, Any]]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def init_board(self, objective: str, tasks: List[str]):
        """Initializes the board with an objective and a list of atomic tasks."""
        if not tasks:
            return
            
        data = []
        for i, task in enumerate(tasks):
            data.append({
                "id": i,
                "description": str(task),
                "state": "todo",
                "result": "",
                "attempts": 0,
                "objective": str(objective)
            })
        self._save(data)

    def get_full_board(self) -> List[Dict[str, Any]]:
        return self._load()

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        board = self._load()
        if not board:
            return None
        
        # Priority: 'doing' first (resume), then 'todo'
        for task in board:
            if task["state"] == "doing":
                return task
        
        for task in board:
            if task["state"] == "todo":
                task["state"] = "doing"
                self._save(board)
                return task
        
        return None

    def update_task_state(self, task_id: int, state: str, result: str = "", increment_attempts: bool = False):
        board = self._load()
        found = False
        for task in board:
            if task["id"] == task_id:
                task["state"] = state
                if result:
                    task["result"] = result
                if increment_attempts:
                    task["attempts"] += 1
                found = True
                break
        
        if found:
            self._save(board)

    def is_complete(self) -> bool:
        board = self._load()
        if not board:
            return False
        return all(task["state"] == "done" for task in board)

if __name__ == "__main__":
    # Test
    k = NomosKanban("/tmp/k_test")
    k.init_board("Objective", ["Task 1", "Task 2"])
    print(f"Next: {k.get_next_task()['description']}")
    k.update_task_state(0, "done")
    print(f"Is complete? {k.is_complete()}")
    print(f"Next: {k.get_next_task()['description']}")
