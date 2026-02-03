from enum import Enum, auto


class Tool(Enum):
    SELECT = auto()
    NODE = auto()
    PIPE = auto()
    SOURCE = auto()
    SINK = auto()
    PUMP = auto()
    VALVE = auto()
