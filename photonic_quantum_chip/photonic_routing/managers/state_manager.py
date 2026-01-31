"""
state_manager.py - State manager
State manager for saving and restoring stage-specific data.
"""

import copy


class StateManager:
    """State manager"""

    def __init__(self):
        self.states = {}

    def save_state(self, stage_name, data_dict):
        """Save state"""
        self.states[stage_name] = copy.deepcopy(data_dict)

    def load_state(self, stage_name):
        """Load state"""
        if stage_name in self.states:
            return copy.deepcopy(self.states[stage_name])
        return None

    def clear(self):
        """Clear all states"""
        self.states.clear()
