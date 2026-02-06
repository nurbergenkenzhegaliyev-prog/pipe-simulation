"""
Demo Multi-Phase Network Example

This example demonstrates how to set up and simulate a simple multi-phase
(gas-liquid) pipe network.

Network topology:
    [Source A] --pipe1--> [Node B] --pipe2--> [Sink C]
    
- Source A: Fixed pressure source (10 bar = 1,000,000 Pa)
- Pipe 1: 100m, 0.1m diameter, liquid + gas flow
- Node B: Junction
- Pipe 2: 150m, 0.08m diameter, liquid + gas flow  
- Sink C: Outlet sink
"""

from app.map.network import PipeNetwork
from app.map.node import Node
from app.map.pipe import Pipe
from app.models.fluid import Fluid
from app.services.pressure import PressureDropService
from app.services.solvers import NetworkSolver, SolverMethod


def create_multiphase_network():
    """Create a simple two-phase flow network"""
    network = PipeNetwork()
    
    # Add nodes
    network.add_node(Node(
        id="Source_A",
        pressure=1_000_000.0,  # 10 bar
        is_source=True,
        elevation=0.0
    ))
    
    network.add_node(Node(
        id="Junction_B",
        elevation=0.0
    ))
    
    network.add_node(Node(
        id="Sink_C",
        is_sink=True,
        elevation=0.0
    ))
    
    # Add pipes with multi-phase flow
    network.add_pipe(Pipe(
        id="Pipe_1",
        start_node="Source_A",
        end_node="Junction_B",
        length=100.0,           # m
        diameter=0.1,           # m (100 mm)
        roughness=0.0045,       # absolute roughness
        liquid_flow_rate=0.015, # m³/s
        gas_flow_rate=0.008     # m³/s
    ))
    
    network.add_pipe(Pipe(
        id="Pipe_2",
        start_node="Junction_B",
        end_node="Sink_C",
        length=150.0,           # m
        diameter=0.08,          # m (80 mm)
        roughness=0.0045,
        liquid_flow_rate=0.015, # m³/s
        gas_flow_rate=0.008     # m³/s
    ))
    
    return network


def main():
    print("=" * 70)
    print("Multi-Phase Flow Network Simulation Demo")
    print("=" * 70)
    
    # Create multi-phase fluid (water-air mixture)
    fluid = Fluid(
        is_multiphase=True,
        liquid_density=998.0,      # kg/m³ (water)
        gas_density=1.2,           # kg/m³ (air at STP)
        liquid_viscosity=1.0e-3,   # Pa·s (water)
        gas_viscosity=1.8e-5,      # Pa·s (air)
        surface_tension=0.072      # N/m (water-air)
    )
    
    print("\n📊 Fluid Properties:")
    print(f"   Type: Multi-phase (liquid-gas)")
    print(f"   Liquid density: {fluid.liquid_density:.1f} kg/m³")
    print(f"   Gas density: {fluid.gas_density:.1f} kg/m³")
    print(f"   Liquid viscosity: {fluid.liquid_viscosity:.4f} Pa·s")
    print(f"   Gas viscosity: {fluid.gas_viscosity:.2e} Pa·s")
    print(f"   Surface tension: {fluid.surface_tension:.4f} N/m")
    
    # Create network
    network = create_multiphase_network()
    
    print("\n🔗 Network Topology:")
    print(f"   Nodes: {len(network.nodes)}")
    print(f"   Pipes: {len(network.pipes)}")
    for node_id, node in network.nodes.items():
        node_type = "Source" if node.is_source else ("Sink" if node.is_sink else "Junction")
        pressure_str = f", P={node.pressure/1e5:.1f} bar" if node.pressure else ""
        print(f"     - {node_id} ({node_type}{pressure_str})")
    
    print("\n🔧 Pipe Configuration:")
    for pipe_id, pipe in network.pipes.items():
        print(f"   {pipe_id}: {pipe.start_node} → {pipe.end_node}")
        print(f"      L={pipe.length}m, D={pipe.diameter*1000:.0f}mm")
        print(f"      Q_liquid={pipe.liquid_flow_rate*1000:.1f} L/s, Q_gas={pipe.gas_flow_rate*1000:.1f} L/s")
        total_q = (pipe.liquid_flow_rate + pipe.gas_flow_rate) * 1000
        liquid_frac = pipe.liquid_flow_rate / (pipe.liquid_flow_rate + pipe.gas_flow_rate) * 100
        print(f"      Total Q={total_q:.1f} L/s, Liquid fraction={liquid_frac:.1f}%")
    
    # Create services
    dp_service = PressureDropService(fluid)
    solver = NetworkPressureSolver(dp_service)
    
    # Run simulation
    print("\n⚙️  Running multi-phase simulation...")
    try:
        solver.solve(network)
        print("✅ Simulation completed successfully!")
        
        # Display results
        print("\n📈 Results:")
        print("\n   Node Pressures:")
        for node_id, node in network.nodes.items():
            if node.pressure is not None:
                pressure_bar = node.pressure / 1e5
                print(f"     {node_id}: {pressure_bar:.3f} bar ({node.pressure:.1f} Pa)")
            else:
                print(f"     {node_id}: Not calculated")
        
        print("\n   Pipe Pressure Drops:")
        for pipe_id, pipe in network.pipes.items():
            if pipe.pressure_drop is not None:
                dp_bar = pipe.pressure_drop / 1e5
                print(f"     {pipe_id}: {dp_bar:.4f} bar ({pipe.pressure_drop:.1f} Pa)")
                
                # Calculate velocities
                A = pipe.area()
                v_liquid = pipe.liquid_flow_rate / A
                v_gas = pipe.gas_flow_rate / A
                v_mixture = v_liquid + v_gas
                print(f"        Superficial velocities: liquid={v_liquid:.2f} m/s, gas={v_gas:.2f} m/s")
                print(f"        Mixture velocity: {v_mixture:.2f} m/s")
            else:
                print(f"     {pipe_id}: Not calculated")
        
        print("\n" + "=" * 70)
        print("Simulation Summary:")
        source_p = network.nodes["Source_A"].pressure / 1e5
        sink_p = network.nodes["Sink_C"].pressure / 1e5 if network.nodes["Sink_C"].pressure else 0
        total_dp = (network.nodes["Source_A"].pressure - (network.nodes["Sink_C"].pressure or 0)) / 1e5
        print(f"   Inlet pressure: {source_p:.3f} bar")
        print(f"   Outlet pressure: {sink_p:.3f} bar")
        print(f"   Total pressure drop: {total_dp:.3f} bar")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
