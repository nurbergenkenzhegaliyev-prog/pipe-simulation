# My Pipesim-like App

A simple PyQt6 app for building and simulating a pipe network (single phase).

## Features
- Draw nodes, pipes, sources, sinks
- Add pumps and valves
- Run simulation and view pressures
- Save/load models as JSON

## Requirements
- Python 3.10+
- PyQt6
- PyQt6-WebEngine

## Setup
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```
python run.py
```

## Notes
- Pumps use a simple pressure ratio model.
- Valves add loss using K * (rho * v^2 / 2).
