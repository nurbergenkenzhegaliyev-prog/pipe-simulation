"""Command manager for undo/redo operations"""

from typing import List, Optional
from abc import ABC, abstractmethod


class Command(ABC):
    """Base class for all commands"""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command"""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Return a description of the command"""
        pass


class CommandManager:
    """Manages command history for undo/redo"""
    
    def __init__(self, max_history: int = 50):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._max_history = max_history
    
    def execute(self, command: Command) -> None:
        """Execute a command and add it to the undo stack"""
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()  # Clear redo stack when new command is executed
        
        # Limit history size
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)
    
    def undo(self) -> Optional[str]:
        """Undo the last command"""
        if not self._undo_stack:
            return None
        
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return command.description()
    
    def redo(self) -> Optional[str]:
        """Redo the last undone command"""
        if not self._redo_stack:
            return None
        
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        return command.description()
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self._redo_stack) > 0
    
    def clear(self) -> None:
        """Clear all command history"""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the command that would be undone"""
        if self._undo_stack:
            return self._undo_stack[-1].description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the command that would be redone"""
        if self._redo_stack:
            return self._redo_stack[-1].description()
        return None
