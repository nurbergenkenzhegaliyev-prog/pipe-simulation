from dataclasses import dataclass

@dataclass
class Node:
    id: str
    pressure: float | None = None
    flow_rate: float | None = None
    elevation: float = 0.0
    is_source: bool = False
    is_sink: bool = False
    is_pump: bool = False
    is_valve: bool = False
    pressure_ratio: float | None = None
    valve_k: float | None = None
