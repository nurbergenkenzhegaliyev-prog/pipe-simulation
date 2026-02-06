from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver, SolverMethod


class MainController:
    def __init__(self, scene):
        self.scene = scene

        # temporary defaults; later from UI dialogs
        self.fluid = Fluid()
        self.solver_method = SolverMethod.NEWTON_RAPHSON  # Default to Newton-Raphson

    def set_fluid(self, fluid: Fluid):
        """Update the fluid properties used for simulations"""
        self.fluid = fluid
    
    def set_solver_method(self, method: SolverMethod):
        """Update the solver method used for simulations"""
        self.solver_method = method

    def build_network_from_scene(self) -> PipeNetwork:
        network = PipeNetwork()

        # Map UI node objects -> node_id
        # Ensure each NodeItem has node_id (e.g. "N1", "N2")
        for node_item in self.scene.nodes:
            n = Node(
                id=node_item.node_id,
                pressure=getattr(node_item, "pressure", None),
                flow_rate=getattr(node_item, "flow_rate", None),
                is_source=getattr(node_item, "is_source", False),
                is_sink=getattr(node_item, "is_sink", False),
                is_pump=getattr(node_item, "is_pump", False),
                is_valve=getattr(node_item, "is_valve", False),
                pressure_ratio=getattr(node_item, "pressure_ratio", None),
                valve_k=getattr(node_item, "valve_k", None),
            )
            network.add_node(n)

        for pipe_item in self.scene.pipes:
            p = Pipe(
                id=pipe_item.pipe_id,
                start_node=pipe_item.node1.node_id,
                end_node=pipe_item.node2.node_id,
                length=pipe_item.length,
                diameter=pipe_item.diameter,
                roughness=getattr(pipe_item, "roughness", 0.005),
                flow_rate=getattr(pipe_item, "flow_rate", 0.05),
                minor_loss_k=getattr(pipe_item, "minor_loss_k", 0.0),
                liquid_flow_rate=getattr(pipe_item, "liquid_flow_rate", None),
                gas_flow_rate=getattr(pipe_item, "gas_flow_rate", None),
                pump_curve=getattr(pipe_item, "pump_curve", None),
                valve=getattr(pipe_item, "valve", None),
            )
            network.add_pipe(p)

        return network

    def run_network_simulation(self):
        network = self.build_network_from_scene()

        dp_service = PressureDropService(self.fluid)
        solver = NetworkSolver(dp_service, method=self.solver_method)
        solver.solve(network)

        return network  # now contains results (pressures & dp)
