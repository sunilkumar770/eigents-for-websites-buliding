
from typing import Dict, Any, Optional
from datetime import datetime

class StatefulTrait:
    def __init__(self):
        self.state: Dict[str, Any] = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_confidence': 0.0,
            'last_execution': None
        }

    def _update_state(self, success: bool, confidence: float):
        self.state['tasks_completed'] += 1 if success else 0
        if success: self.state['total_confidence'] += confidence
        else: self.state['tasks_failed'] += 1
        self.state['last_execution'] = datetime.now().isoformat()
