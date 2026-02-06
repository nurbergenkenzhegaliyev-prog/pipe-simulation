import logging
from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver

# Configure logging
# Configure logging to always print to console, even with pytest
logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)
logger = logging.getLogger(__name__)


def test_pressure_drop_propagation():
    network = PipeNetwork()

    network.add_node(Node(id="A", pressure=10e6, is_source=True))
    network.add_node(Node(id="B"))
    network.add_node(Node(id="C"))

    network.add_pipe(Pipe(
        id="P1",
        start_node="A",
        end_node="B",
        length=1000,
        diameter=0.2,
        roughness=0.005,
        flow_rate=0.05
    ))

    network.add_pipe(Pipe(
        id="P2",
        start_node="B",
        end_node="C",
        length=500,
        diameter=0.15,
        roughness=0.005,
        flow_rate=0.05
    ))

    fluid = Fluid()
    dp_service = PressureDropService(fluid)
    solver = NetworkSolver(dp_service)

    solver.solve(network)

    # ---- LOG RESULTS ----
    logger.info("\n=== NODE PRESSURES ===")
    for node_id, node in network.nodes.items():
        logger.info(f"Node {node_id}: {node.pressure:,.2f} Pa")

    logger.info("\n=== PIPE PRESSURE DROPS ===")
    for pipe_id, pipe in network.pipes.items():
        logger.info(f"Pipe {pipe_id}: dP = {pipe.pressure_drop:,.2f} Pa")

    # ---- ASSERTIONS ----
    assert network.nodes["B"].pressure < network.nodes["A"].pressure
    assert network.nodes["C"].pressure < network.nodes["B"].pressure
