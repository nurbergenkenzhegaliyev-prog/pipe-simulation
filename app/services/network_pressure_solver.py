from typing import Optional

from app.map.network import PipeNetwork
from app.services.pressure_drop_service import PressureDropService
from app.services.solver_components import CycleFinder, HardyCrossSolver, PressurePropagation


class NetworkPressureSolver:
    def __init__(
        self,
        dp_service: PressureDropService,
        cycle_finder: Optional[CycleFinder] = None,
        hardy_cross: Optional[HardyCrossSolver] = None,
        propagator: Optional[PressurePropagation] = None,
    ):
        self.dp_service = dp_service
        self.cycle_finder = cycle_finder or CycleFinder()
        self.hardy_cross = hardy_cross or HardyCrossSolver(dp_service)
        self.propagator = propagator or PressurePropagation(dp_service)

    def solve(self, network: PipeNetwork):
        cycles = self.cycle_finder.find_cycles(network)
        if cycles:
            self.hardy_cross.apply(network, cycles)

        self.propagator.propagate(network)
