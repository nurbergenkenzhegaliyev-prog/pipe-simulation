import math

from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService


def test_minor_loss_increases_pressure_drop():
	fluid = Fluid(density=1000.0, viscosity=1e-3)
	service = PressureDropService(fluid)

	base_pipe = Pipe(
		id="P1",
		start_node="N1",
		end_node="N2",
		length=100.0,
		diameter=0.2,
		roughness=0.0001,
		flow_rate=0.05,
		minor_loss_k=0.0,
	)

	loss_pipe = Pipe(
		id="P2",
		start_node="N1",
		end_node="N2",
		length=100.0,
		diameter=0.2,
		roughness=0.0001,
		flow_rate=0.05,
		minor_loss_k=5.0,
	)

	dp_base = service.calculate_pipe_dp(base_pipe)
	dp_loss = service.calculate_pipe_dp(loss_pipe)

	v = base_pipe.flow_rate / base_pipe.area()
	expected_extra = loss_pipe.minor_loss_k * (fluid.density * v**2 / 2)

	assert dp_loss > dp_base
	assert math.isclose(dp_loss - dp_base, expected_extra, rel_tol=1e-6)


def test_temperature_reduces_viscosity_and_pressure_drop():
	base_fluid = Fluid(
		density=998.0,
		viscosity=1e-3,
		temperature_c=20.0,
		reference_temperature_c=20.0,
		reference_density=998.0,
		reference_viscosity=1e-3,
	)
	hot_fluid = Fluid(
		density=998.0,
		viscosity=1e-3,
		temperature_c=60.0,
		reference_temperature_c=20.0,
		reference_density=998.0,
		reference_viscosity=1e-3,
	)

	pipe = Pipe(
		id="P3",
		start_node="N1",
		end_node="N2",
		length=200.0,
		diameter=0.2,
		roughness=0.0001,
		flow_rate=0.05,
	)

	base_service = PressureDropService(base_fluid)
	hot_service = PressureDropService(hot_fluid)

	dp_base = base_service.calculate_pipe_dp(pipe)
	dp_hot = hot_service.calculate_pipe_dp(pipe)

	assert hot_fluid.effective_viscosity() < base_fluid.effective_viscosity()
	assert dp_hot < dp_base
