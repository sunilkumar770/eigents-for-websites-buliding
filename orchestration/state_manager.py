"""
State Manager

Manages workflow state persistence and recovery.
Supports SQLite for local development and PostgreSQL for production.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import logging


class WorkflowStatus(Enum):
    """Workflow status states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(Enum):
    """Individual stage status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowState:
    """Workflow state snapshot"""
    project_id: str
    status: WorkflowStatus
    current_stage: str
    prompt: str
    context: Dict[str, Any]
    stage_results: Dict[str, Any]
    errors: List[str]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


@dataclass
class StageState:
    """Individual stage state"""
    project_id: str
    stage_name: str
    status: StageStatus
    agent_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    retry_count: int
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class StateManager:
    """
    Manages workflow state persistence.
    
    Features:
    - SQLite for local development
    - State snapshots at each stage
    - Rollback capability
    - State export/import
    """
    
    def __init__(self, db_path: str = "workflow_state.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                project_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                prompt TEXT NOT NULL,
                context TEXT,
                stage_results TEXT,
                errors TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Stages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                stage_name TEXT NOT NULL,
                status TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                inputs TEXT,
                outputs TEXT,
                confidence REAL,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES workflows(project_id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_status 
            ON workflows(project_id, status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stage_project 
            ON stages(project_id, stage_name)
        """)
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Database initialized at {self.db_path}")
    
    def create_workflow(
        self,
        project_id: str,
        prompt: str,
        context: Dict[str, Any] = None
    ) -> WorkflowState:
        """Create a new workflow"""
        
        now = datetime.utcnow().isoformat()
        
        state = WorkflowState(
            project_id=project_id,
            status=WorkflowStatus.IDLE,
            current_stage="product_interpretation",
            prompt=prompt,
            context=context or {},
            stage_results={},
            errors=[],
            created_at=now,
            updated_at=now,
            metadata={}
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflows 
            (project_id, status, current_stage, prompt, context, stage_results, 
             errors, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            state.project_id,
            state.status.value,
            state.current_stage,
            state.prompt,
            json.dumps(state.context),
            json.dumps(state.stage_results),
            json.dumps(state.errors),
            state.created_at,
            state.updated_at,
            json.dumps(state.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Created workflow {project_id}")
        return state
    
    def get_workflow(self, project_id: str) -> Optional[WorkflowState]:
        """Get workflow state"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT project_id, status, current_stage, prompt, context, 
                   stage_results, errors, created_at, updated_at, metadata
            FROM workflows
            WHERE project_id = ?
        """, (project_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return WorkflowState(
            project_id=row[0],
            status=WorkflowStatus(row[1]),
            current_stage=row[2],
            prompt=row[3],
            context=json.loads(row[4]) if row[4] else {},
            stage_results=json.loads(row[5]) if row[5] else {},
            errors=json.loads(row[6]) if row[6] else [],
            created_at=row[7],
            updated_at=row[8],
            metadata=json.loads(row[9]) if row[9] else {}
        )
    
    def update_workflow(self, state: WorkflowState):
        """Update workflow state"""
        
        state.updated_at = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflows
            SET status = ?, current_stage = ?, stage_results = ?, 
                errors = ?, updated_at = ?, metadata = ?
            WHERE project_id = ?
        """, (
            state.status.value,
            state.current_stage,
            json.dumps(state.stage_results),
            json.dumps(state.errors),
            state.updated_at,
            json.dumps(state.metadata),
            state.project_id
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.debug(f"Updated workflow {state.project_id}")
    
    def save_stage(self, stage: StageState):
        """Save stage state"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stages
            (project_id, stage_name, status, agent_type, inputs, outputs,
             confidence, retry_count, error_message, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stage.project_id,
            stage.stage_name,
            stage.status.value,
            stage.agent_type,
            json.dumps(stage.inputs),
            json.dumps(stage.outputs),
            stage.confidence,
            stage.retry_count,
            stage.error_message,
            stage.started_at,
            stage.completed_at
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.debug(f"Saved stage {stage.stage_name} for {stage.project_id}")
    
    def get_stages(self, project_id: str) -> List[StageState]:
        """Get all stages for a workflow"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT project_id, stage_name, status, agent_type, inputs, outputs,
                   confidence, retry_count, error_message, started_at, completed_at
            FROM stages
            WHERE project_id = ?
            ORDER BY id ASC
        """, (project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        stages = []
        for row in rows:
            stages.append(StageState(
                project_id=row[0],
                stage_name=row[1],
                status=StageStatus(row[2]),
                agent_type=row[3],
                inputs=json.loads(row[4]) if row[4] else {},
                outputs=json.loads(row[5]) if row[5] else {},
                confidence=row[6] or 0.0,
                retry_count=row[7] or 0,
                error_message=row[8],
                started_at=row[9],
                completed_at=row[10]
            ))
        
        return stages
    
    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100
    ) -> List[WorkflowState]:
        """List workflows with optional status filter"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT project_id, status, current_stage, prompt, context,
                       stage_results, errors, created_at, updated_at, metadata
                FROM workflows
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status.value, limit))
        else:
            cursor.execute("""
                SELECT project_id, status, current_stage, prompt, context,
                       stage_results, errors, created_at, updated_at, metadata
                FROM workflows
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        workflows = []
        for row in rows:
            workflows.append(WorkflowState(
                project_id=row[0],
                status=WorkflowStatus(row[1]),
                current_stage=row[2],
                prompt=row[3],
                context=json.loads(row[4]) if row[4] else {},
                stage_results=json.loads(row[5]) if row[5] else {},
                errors=json.loads(row[6]) if row[6] else [],
                created_at=row[7],
                updated_at=row[8],
                metadata=json.loads(row[9]) if row[9] else {}
            ))
        
        return workflows
    
    def delete_workflow(self, project_id: str):
        """Delete a workflow and all its stages"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM stages WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM workflows WHERE project_id = ?", (project_id,))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Deleted workflow {project_id}")
    
    def export_workflow(self, project_id: str) -> Dict[str, Any]:
        """Export workflow state for debugging"""
        
        workflow = self.get_workflow(project_id)
        if not workflow:
            return {}
        
        stages = self.get_stages(project_id)
        
        return {
            'workflow': asdict(workflow),
            'stages': [asdict(s) for s in stages]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count workflows by status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM workflows 
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # Total workflows
        cursor.execute("SELECT COUNT(*) FROM workflows")
        total_workflows = cursor.fetchone()[0]
        
        # Total stages
        cursor.execute("SELECT COUNT(*) FROM stages")
        total_stages = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_workflows': total_workflows,
            'total_stages': total_stages,
            'status_counts': status_counts
        }


if __name__ == '__main__':
    # Test the state manager
    logging.basicConfig(level=logging.INFO)
    
    manager = StateManager("test_workflow.db")
    
    # Create workflow
    state = manager.create_workflow(
        project_id="test-123",
        prompt="Build a recipe app",
        context={'target_audience': 'home cooks'}
    )
    
    print(f"Created workflow: {state.project_id}")
    
    # Update workflow
    state.status = WorkflowStatus.RUNNING
    state.current_stage = "frontend_generation"
    manager.update_workflow(state)
    
    # Save stage
    stage = StageState(
        project_id="test-123",
        stage_name="product_interpretation",
        status=StageStatus.COMPLETED,
        agent_type="product_interpreter",
        inputs={'prompt': 'Build a recipe app'},
        outputs={'product_name': 'Recipe App'},
        confidence=95.0,
        retry_count=0,
        error_message=None,
        started_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat()
    )
    manager.save_stage(stage)
    
    # Retrieve
    retrieved = manager.get_workflow("test-123")
    print(f"Retrieved workflow: {retrieved.status.value}")
    
    stages = manager.get_stages("test-123")
    print(f"Stages: {len(stages)}")
    
    # Statistics
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")
