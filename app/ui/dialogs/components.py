from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox


class DialogUiFactory:
    @staticmethod
    def create_double_spin(
        *,
        decimals: int,
        min_value: float,
        max_value: float,
        value: float,
        suffix: str | None = None,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setDecimals(decimals)
        spin.setRange(min_value, max_value)
        spin.setValue(float(value))
        if suffix:
            spin.setSuffix(suffix)
        return spin

    @staticmethod
    def create_button_box(dialog: QDialog) -> QDialogButtonBox:
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        return buttons


@dataclass
class FluidSinglePhaseSection:
    group: QGroupBox
    density_spin: QDoubleSpinBox
    viscosity_spin: QDoubleSpinBox

    @classmethod
    def from_fluid(cls, fluid) -> "FluidSinglePhaseSection":
        group = QGroupBox("Single-Phase Properties")
        form = QFormLayout()

        density_spin = DialogUiFactory.create_double_spin(
            decimals=2,
            min_value=0.1,
            max_value=1e5,
            value=fluid.density,
            suffix=" kg/m³",
        )
        viscosity_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=1e-7,
            max_value=1.0,
            value=fluid.viscosity,
            suffix=" Pa·s",
        )

        form.addRow("Density", density_spin)
        form.addRow("Viscosity", viscosity_spin)
        group.setLayout(form)
        return cls(group=group, density_spin=density_spin, viscosity_spin=viscosity_spin)


@dataclass
class FluidMultiPhaseSection:
    group: QGroupBox
    liquid_density_spin: QDoubleSpinBox
    gas_density_spin: QDoubleSpinBox
    liquid_viscosity_spin: QDoubleSpinBox
    gas_viscosity_spin: QDoubleSpinBox
    surface_tension_spin: QDoubleSpinBox

    @classmethod
    def from_fluid(cls, fluid) -> "FluidMultiPhaseSection":
        group = QGroupBox("Multi-Phase Properties")
        form = QFormLayout()

        liquid_density_spin = DialogUiFactory.create_double_spin(
            decimals=2,
            min_value=0.1,
            max_value=1e5,
            value=fluid.liquid_density,
            suffix=" kg/m³",
        )
        gas_density_spin = DialogUiFactory.create_double_spin(
            decimals=3,
            min_value=0.001,
            max_value=1000.0,
            value=fluid.gas_density,
            suffix=" kg/m³",
        )
        liquid_viscosity_spin = DialogUiFactory.create_double_spin(
            decimals=6,
            min_value=1e-7,
            max_value=1.0,
            value=fluid.liquid_viscosity,
            suffix=" Pa·s",
        )
        gas_viscosity_spin = DialogUiFactory.create_double_spin(
            decimals=8,
            min_value=1e-9,
            max_value=1e-3,
            value=fluid.gas_viscosity,
            suffix=" Pa·s",
        )
        surface_tension_spin = DialogUiFactory.create_double_spin(
            decimals=4,
            min_value=0.0,
            max_value=1.0,
            value=fluid.surface_tension,
            suffix=" N/m",
        )

        form.addRow("Liquid Density", liquid_density_spin)
        form.addRow("Gas Density", gas_density_spin)
        form.addRow("Liquid Viscosity", liquid_viscosity_spin)
        form.addRow("Gas Viscosity", gas_viscosity_spin)
        form.addRow("Surface Tension", surface_tension_spin)
        group.setLayout(form)
        return cls(
            group=group,
            liquid_density_spin=liquid_density_spin,
            gas_density_spin=gas_density_spin,
            liquid_viscosity_spin=liquid_viscosity_spin,
            gas_viscosity_spin=gas_viscosity_spin,
            surface_tension_spin=surface_tension_spin,
        )

    def set_enabled(self, enabled: bool) -> None:
        self.group.setEnabled(enabled)
