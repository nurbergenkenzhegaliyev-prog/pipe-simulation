import logging

from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure_drop_components import (
    FlowProperties,
    MultiPhasePressureDrop,
    NodePressureGain,
    SinglePhasePressureDrop,
)


# Configure logging
# Configure logging to always print to console, even with pytest
logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)
logger = logging.getLogger(__name__)


class PressureDropService:
    def __init__(
        self,
        fluid: Fluid,
        flow: FlowProperties | None = None,
        single_phase: SinglePhasePressureDrop | None = None,
        multi_phase: MultiPhasePressureDrop | None = None,
        node_gain: NodePressureGain | None = None,
    ):
        self.fluid = fluid
        self.flow = flow or FlowProperties()
        self.single_phase = single_phase or SinglePhasePressureDrop(self.flow)
        self.multi_phase = multi_phase or MultiPhasePressureDrop(self.flow)
        self.node_gain = node_gain or NodePressureGain()

    def calculate_pipe_dp(self, pipe: Pipe) -> float:
        if self.fluid.is_multiphase:
            return self.multi_phase.calculate(pipe, self.fluid)
        return self.single_phase.calculate(pipe, self.fluid)

    def calculate_multiphase_dp(self, pipe: Pipe) -> float:
        return self.multi_phase.calculate(pipe, self.fluid)

    def valve_loss(self, k: float, pipe: Pipe) -> float:
        if pipe.flow_rate is None:
            raise ValueError(f"Pipe {pipe.id} has no flow rate")
        rho = self.fluid.density
        v = pipe.flow_rate / pipe.area()
        return k * (rho * v**2 / 2)

    def calculate_node_pressure_gain(self, node, inlet_pressure: float) -> float:
        return self.node_gain.calculate(node, inlet_pressure)
