import lancedb
import pandas as pd
import os
from typing import List, Dict, Any, Optional

class NomosKanban:
    def __init__(self, db_path: str, table_name: str = "workspace_kanban"):
        self.db = lancedb.connect(db_path)
        self.table_name = table_name

    def init_board(self, objective: str, tasks: List[str]):
        """Initializes the board with an objective and a list of atomic tasks."""
        data = []
        for i, task in enumerate(tasks):
            data.append({
                "id": i,
                "description": task,
                "state": "todo",
                "result": "",
                "attempts": 0,
                "objective": objective
            })
        
        df = pd.DataFrame(data)
        # Force overwrite to start fresh for a new objective
        self.db.create_table(self.table_name, data=df, mode="overwrite")

    def get_full_board(self) -> List[Dict[str, Any]]:
        if self.table_name not in self.db.list_tables():
            return []
        table = self.db.open_table(self.table_name)
        return table.to_pandas().to_dict('records')

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        if self.table_name not in self.db.list_tables():
            return None
        
        table = self.db.open_table(self.table_name)
        df = table.to_pandas()
        
        # Priority: 'doing' first (resume), then 'todo'
        doing = df[df['state'] == 'doing']
        if not doing.empty:
            return doing.iloc[0].to_dict()
        
        todo = df[df['state'] == 'todo']
        if not todo.empty:
            next_task = todo.iloc[0].to_dict()
            self.update_task_state(next_task['id'], "doing")
            return next_task
        
        return None

    def update_task_state(self, task_id: int, state: str, result: str = "", increment_attempts: bool = False):
        if self.table_name not in self.db.list_tables():
            return
        
        table = self.db.open_table(self.table_name)
        df = table.to_pandas()
        
        if task_id in df['id'].values:
            idx = df[df['id'] == task_id].index[0]
            df.at[idx, 'state'] = state
            if result:
                df.at[idx, 'result'] = result
            if increment_attempts:
                df.at[idx, 'attempts'] += 1
            
            # Update the table
            self.db.create_table(self.table_name, data=df, mode="overwrite")

    def is_complete(self) -> bool:
        if self.table_name not in self.db.list_tables():
            return True
        table = self.db.open_table(self.table_name)
        df = table.to_pandas()
        return all(df['state'] == 'done')

if __name__ == "__main__":
    # Small test
    import shutil
    test_db = "/tmp/nomos_kanban_test"
    if os.path.exists(test_db):
        shutil.rmtree(test_db)
    os.makedirs(test_db)
    
    kanban = NomosKanban(test_db)
    kanban.init_board("Build Calculator", ["T1: Setup", "T2: Code"])
    
    task = kanban.get_next_task()
    print(f"Next: {task['description']} (State: {task['state']})")
    
    kanban.update_task_state(task['id'], "done", "Finished setup")
    print(f"Is Complete? {kanban.is_complete()}")
    
    task2 = kanban.get_next_task()
    print(f"Next: {task2['description']} (State: {task2['state']})")
