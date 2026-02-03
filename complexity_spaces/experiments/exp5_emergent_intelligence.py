"""
Experiment 5: Emergent Intelligence from Complexity Space Interactions

From the document:
"Intelligence needs redundancy to give it room to move."
"Each layer can have its own patterns, and the direction is two way."

This experiment explores:
1. How agency emerges from over-specification
2. Patterns as the substrate of intelligence
3. Bioelectric-style signaling across complexity layers
"""

import sys
sys.path.insert(0, '/home/user/TestRepo/complexity_spaces')

from core import Measure, Point, Segment, Certainty
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable, Set
from enum import Enum, auto
from collections import defaultdict


# ============================================================================
# AGENCY FROM REDUNDANCY
# ============================================================================

@dataclass
class RedundantPoint:
    """
    A point with multiple ways to specify its position.

    From the document: "You can't expect a layer to be 'smart' without
    giving them options on how to accommodate requests, so this
    redundancy is actually a key feature."
    """
    # Primary position
    x: float
    y: float

    # Redundant specifications (any can influence final position)
    center_of_segment: Optional[Tuple[float, float, float, float]] = None  # (x1,y1,x2,y2)
    center_of_triangle: Optional[List[Tuple[float, float]]] = None  # 3 vertices
    on_circle: Optional[Tuple[float, float, float, float]] = None  # (cx, cy, r, angle)

    # Weight of each specification
    weights: Dict[str, float] = field(default_factory=lambda: {
        'direct': 1.0,
        'segment': 0.0,
        'triangle': 0.0,
        'circle': 0.0
    })

    def compute_position(self) -> Tuple[float, float]:
        """
        Compute position as weighted average of all specifications.
        This is where "agency" emerges - the point can balance constraints.
        """
        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0

        # Direct position
        if self.weights['direct'] > 0:
            weighted_x += self.x * self.weights['direct']
            weighted_y += self.y * self.weights['direct']
            total_weight += self.weights['direct']

        # Segment center
        if self.center_of_segment and self.weights['segment'] > 0:
            x1, y1, x2, y2 = self.center_of_segment
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            weighted_x += cx * self.weights['segment']
            weighted_y += cy * self.weights['segment']
            total_weight += self.weights['segment']

        # Triangle centroid
        if self.center_of_triangle and self.weights['triangle'] > 0:
            cx = sum(p[0] for p in self.center_of_triangle) / 3
            cy = sum(p[1] for p in self.center_of_triangle) / 3
            weighted_x += cx * self.weights['triangle']
            weighted_y += cy * self.weights['triangle']
            total_weight += self.weights['triangle']

        # Point on circle
        if self.on_circle and self.weights['circle'] > 0:
            cx, cy, r, angle = self.on_circle
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            weighted_x += px * self.weights['circle']
            weighted_y += py * self.weights['circle']
            total_weight += self.weights['circle']

        if total_weight > 0:
            return (weighted_x / total_weight, weighted_y / total_weight)
        return (self.x, self.y)

    def degrees_of_freedom(self) -> int:
        """
        Count active degrees of freedom.
        More redundancy = more DOF = more agency.
        """
        dof = 0
        if self.weights['direct'] > 0:
            dof += 2
        if self.center_of_segment and self.weights['segment'] > 0:
            dof += 4  # Segment endpoints
        if self.center_of_triangle and self.weights['triangle'] > 0:
            dof += 6  # Three vertices
        if self.on_circle and self.weights['circle'] > 0:
            dof += 4  # Center, radius, angle
        return dof


# ============================================================================
# PATTERNS AS INTELLIGENCE SUBSTRATE
# ============================================================================

class Pattern:
    """
    A pattern that layers can recognize and try to satisfy.

    From the document: "Patterns are able to be expressed in each layer
    in their own way... they come from logic, order, memory, and
    ultimately experience in the environment."
    """

    def __init__(self, name: str, test_fn: Callable, description: str = ""):
        self.name = name
        self.test_fn = test_fn
        self.description = description

    def satisfaction(self, elements: List[any]) -> float:
        """Returns 0-1 indicating how well pattern is satisfied."""
        return self.test_fn(elements)


# Common patterns
def symmetry_pattern(points: List[Tuple[float, float]]) -> float:
    """Test for bilateral symmetry around centroid."""
    if len(points) < 2:
        return 1.0

    # Find centroid
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)

    # Measure symmetry by comparing distances
    distances = [math.sqrt((p[0]-cx)**2 + (p[1]-cy)**2) for p in points]
    if max(distances) == 0:
        return 1.0

    variance = sum((d - sum(distances)/len(distances))**2 for d in distances) / len(distances)
    return 1.0 / (1.0 + variance)


def evenspacing_pattern(points: List[Tuple[float, float]]) -> float:
    """Test for even spacing between points."""
    if len(points) < 3:
        return 1.0

    # Calculate all pairwise distances
    distances = []
    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i < j:
                d = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
                distances.append(d)

    if not distances:
        return 1.0

    avg_dist = sum(distances) / len(distances)
    variance = sum((d - avg_dist)**2 for d in distances) / len(distances)
    return 1.0 / (1.0 + variance / (avg_dist + 0.001))


def ordering_pattern(values: List[float]) -> float:
    """Test if values are in ascending order."""
    if len(values) < 2:
        return 1.0

    in_order = sum(1 for i in range(len(values)-1) if values[i] <= values[i+1])
    return in_order / (len(values) - 1)


# ============================================================================
# BIOELECTRIC-STYLE SIGNALING
# ============================================================================

@dataclass
class Signal:
    """
    A signal that propagates across layers.

    From the document: "these patterns ultimately are represented by
    equations of some sort, which are in reality just numbering
    systems of their own."
    """
    source_layer: int
    pattern: str
    strength: float
    direction: List[float]  # Gradient direction
    decay_rate: float = 0.9


class SignalingLayer:
    """
    A layer that can send and receive signals.

    Each layer interprets signals in its own dimensional context.
    """

    def __init__(self, layer_id: int, dimension: int):
        self.layer_id = layer_id
        self.dimension = dimension
        self.elements: List[List[float]] = []  # Elements in this layer
        self.incoming_signals: List[Signal] = []
        self.outgoing_signals: List[Signal] = []
        self.patterns: List[Pattern] = []

    def add_element(self, coords: List[float]):
        """Add an element to this layer."""
        if len(coords) == self.dimension:
            self.elements.append(coords)
        else:
            # Project or embed as needed
            if len(coords) < self.dimension:
                coords = coords + [0.0] * (self.dimension - len(coords))
            else:
                coords = coords[:self.dimension]
            self.elements.append(coords)

    def add_pattern(self, pattern: Pattern):
        """Add a pattern this layer recognizes."""
        self.patterns.append(pattern)

    def receive_signal(self, signal: Signal):
        """Receive a signal from another layer."""
        self.incoming_signals.append(signal)

    def interpret_signal(self, signal: Signal) -> List[float]:
        """
        Interpret a signal in this layer's dimensional context.

        A 3D layer sees a 2D signal as having z=0.
        A 1D layer sees a 2D signal as a projection.
        """
        direction = signal.direction

        if len(direction) < self.dimension:
            # Embed: add zeros
            return direction + [0.0] * (self.dimension - len(direction))
        elif len(direction) > self.dimension:
            # Project: take first n components
            return direction[:self.dimension]
        return direction

    def compute_pattern_forces(self) -> Dict[int, List[float]]:
        """
        Compute forces on elements based on pattern satisfaction.
        """
        forces = {i: [0.0] * self.dimension for i in range(len(self.elements))}

        for pattern in self.patterns:
            # Compute satisfaction
            if self.dimension == 2:
                points = [(e[0], e[1]) for e in self.elements]
                satisfaction = pattern.satisfaction(points)
            else:
                # Use first two dimensions for geometric patterns
                points = [(e[0], e[1] if len(e) > 1 else 0) for e in self.elements]
                satisfaction = pattern.satisfaction(points)

            # If not satisfied, compute gradient toward satisfaction
            if satisfaction < 0.95:
                # Simple gradient: move toward centroid for symmetry
                if pattern.name == "symmetry":
                    cx = sum(e[0] for e in self.elements) / len(self.elements)
                    cy = sum(e[1] if len(e) > 1 else 0 for e in self.elements) / len(self.elements)

                    for i, elem in enumerate(self.elements):
                        dx = cx - elem[0]
                        dy = (cy - elem[1]) if len(elem) > 1 else 0
                        dist = math.sqrt(dx**2 + dy**2) + 0.001
                        forces[i][0] += dx / dist * (1 - satisfaction)
                        if len(forces[i]) > 1:
                            forces[i][1] += dy / dist * (1 - satisfaction)

        return forces

    def emit_signal(self) -> Optional[Signal]:
        """
        Emit a signal based on current state.
        """
        if not self.patterns or not self.elements:
            return None

        # Find least satisfied pattern
        min_satisfaction = 1.0
        least_satisfied = None

        for pattern in self.patterns:
            if self.dimension >= 2:
                points = [(e[0], e[1]) for e in self.elements]
            else:
                points = [(e[0], 0) for e in self.elements]
            sat = pattern.satisfaction(points)
            if sat < min_satisfaction:
                min_satisfaction = sat
                least_satisfied = pattern

        if least_satisfied and min_satisfaction < 0.9:
            # Compute gradient direction
            forces = self.compute_pattern_forces()
            avg_force = [0.0] * self.dimension
            for force in forces.values():
                for d in range(self.dimension):
                    avg_force[d] += force[d]

            norm = math.sqrt(sum(f**2 for f in avg_force)) + 0.001
            direction = [f/norm for f in avg_force]

            return Signal(
                source_layer=self.layer_id,
                pattern=least_satisfied.name,
                strength=1 - min_satisfaction,
                direction=direction
            )

        return None


class MultiLayerIntelligence:
    """
    A system where intelligence emerges from layer interactions.
    """

    def __init__(self):
        self.layers: Dict[int, SignalingLayer] = {}
        self.history: List[Dict] = []

    def add_layer(self, layer_id: int, dimension: int) -> SignalingLayer:
        layer = SignalingLayer(layer_id, dimension)
        self.layers[layer_id] = layer
        return layer

    def step(self):
        """
        Perform one step of the intelligence system.

        1. Each layer emits signals
        2. Signals propagate to adjacent layers
        3. Layers interpret signals and adjust elements
        """
        # Collect all signals
        all_signals = []
        for layer in self.layers.values():
            signal = layer.emit_signal()
            if signal:
                all_signals.append(signal)
                layer.outgoing_signals.append(signal)

        # Propagate signals to other layers
        for signal in all_signals:
            for layer_id, layer in self.layers.items():
                if layer_id != signal.source_layer:
                    # Decay signal based on "distance" between layers
                    distance = abs(layer_id - signal.source_layer)
                    decayed_signal = Signal(
                        source_layer=signal.source_layer,
                        pattern=signal.pattern,
                        strength=signal.strength * (signal.decay_rate ** distance),
                        direction=signal.direction,
                        decay_rate=signal.decay_rate
                    )
                    layer.receive_signal(decayed_signal)

        # Each layer responds to signals
        for layer in self.layers.values():
            # Combine pattern forces with signal forces
            pattern_forces = layer.compute_pattern_forces()

            for signal in layer.incoming_signals:
                interpreted = layer.interpret_signal(signal)
                for i in range(len(layer.elements)):
                    for d in range(layer.dimension):
                        pattern_forces[i][d] += interpreted[d] * signal.strength * 0.1

            # Apply forces to elements
            for i, elem in enumerate(layer.elements):
                for d in range(layer.dimension):
                    elem[d] += pattern_forces[i][d] * 0.1

            layer.incoming_signals.clear()

        # Record history
        self.history.append({
            layer_id: [(e[0], e[1] if len(e) > 1 else 0) for e in layer.elements]
            for layer_id, layer in self.layers.items()
        })

    def run(self, steps: int = 50):
        """Run the system for multiple steps."""
        for _ in range(steps):
            self.step()


# ============================================================================
# EXPERIMENTS
# ============================================================================

def experiment_redundancy_creates_agency():
    """
    Experiment: Points with more specification options have more agency.
    """
    print("=" * 60)
    print("EXPERIMENT: Redundancy Creates Agency")
    print("=" * 60)

    # Point with minimal specification
    simple_point = RedundantPoint(x=50, y=50)
    simple_point.weights = {'direct': 1.0, 'segment': 0, 'triangle': 0, 'circle': 0}

    print(f"\nSimple point (direct only):")
    print(f"  DOF: {simple_point.degrees_of_freedom()}")
    print(f"  Position: {simple_point.compute_position()}")
    print(f"  Agency: None (fixed position)")

    # Point with multiple specifications
    complex_point = RedundantPoint(x=50, y=50)
    complex_point.center_of_segment = (30, 40, 70, 60)  # Midpoint at (50, 50)
    complex_point.on_circle = (50, 50, 20, 0)  # Point at (70, 50)
    complex_point.weights = {'direct': 0.5, 'segment': 0.3, 'triangle': 0, 'circle': 0.2}

    print(f"\nComplex point (multiple specs):")
    print(f"  DOF: {complex_point.degrees_of_freedom()}")
    print(f"  Position: {complex_point.compute_position()}")
    print(f"  Agency: Can balance between specifications")

    # Demonstrate agency by changing weights
    print(f"\n  Changing weights to favor circle...")
    complex_point.weights = {'direct': 0.1, 'segment': 0.1, 'triangle': 0, 'circle': 0.8}
    print(f"  New position: {complex_point.compute_position()}")

    print(f"\n  Changing weights to favor segment...")
    complex_point.weights = {'direct': 0.1, 'segment': 0.8, 'triangle': 0, 'circle': 0.1}
    print(f"  New position: {complex_point.compute_position()}")

    print("\nInsight: Redundancy = options = agency")


def experiment_patterns_as_attractors():
    """
    Experiment: Patterns act as attractors for configurations.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Patterns as Attractors")
    print("=" * 60)

    # Random initial points
    random.seed(42)
    points = [(random.uniform(20, 80), random.uniform(20, 80)) for _ in range(5)]

    print(f"\nInitial random points: {[(f'{p[0]:.1f}', f'{p[1]:.1f}') for p in points]}")

    # Test patterns
    patterns = [
        Pattern("symmetry", symmetry_pattern),
        Pattern("even_spacing", evenspacing_pattern),
    ]

    for pattern in patterns:
        satisfaction = pattern.satisfaction(points)
        print(f"\n{pattern.name} satisfaction: {satisfaction:.3f}")

    # Simulate movement toward pattern satisfaction
    print("\n--- Evolving toward patterns ---")
    learning_rate = 0.1

    for iteration in range(20):
        # Compute centroid
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)

        # Move each point toward centroid (increases symmetry)
        new_points = []
        for p in points:
            dx = cx - p[0]
            dy = cy - p[1]
            new_x = p[0] + dx * learning_rate * 0.5
            new_y = p[1] + dy * learning_rate * 0.5
            new_points.append((new_x, new_y))
        points = new_points

        if iteration % 5 == 0:
            sym_sat = symmetry_pattern(points)
            print(f"  Iteration {iteration}: symmetry = {sym_sat:.3f}")

    print(f"\nFinal points: {[(f'{p[0]:.1f}', f'{p[1]:.1f}') for p in points]}")


def experiment_cross_layer_communication():
    """
    Experiment: Signals propagate between layers of different dimensions.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Cross-Layer Communication")
    print("=" * 60)

    system = MultiLayerIntelligence()

    # Create layers of different dimensions
    layer_1d = system.add_layer(0, 1)  # 1D layer
    layer_2d = system.add_layer(1, 2)  # 2D layer
    layer_3d = system.add_layer(2, 3)  # 3D layer

    # Add elements to each layer
    layer_1d.add_element([10])
    layer_1d.add_element([30])
    layer_1d.add_element([50])

    layer_2d.add_element([20, 20])
    layer_2d.add_element([60, 40])
    layer_2d.add_element([40, 70])

    layer_3d.add_element([30, 30, 30])
    layer_3d.add_element([50, 50, 50])
    layer_3d.add_element([70, 70, 70])

    # Add patterns
    sym_pattern = Pattern("symmetry", symmetry_pattern)
    layer_2d.add_pattern(sym_pattern)

    print("\nInitial state:")
    for layer_id, layer in system.layers.items():
        print(f"  Layer {layer_id} ({layer.dimension}D): {layer.elements}")

    # Run simulation
    system.run(steps=30)

    print(f"\nAfter 30 steps:")
    for layer_id, layer in system.layers.items():
        print(f"  Layer {layer_id} ({layer.dimension}D): {[f'({e[0]:.1f}, {e[1] if len(e)>1 else 0:.1f})' for e in layer.elements]}")

    # Measure pattern satisfaction
    points_2d = [(e[0], e[1]) for e in layer_2d.elements]
    final_symmetry = symmetry_pattern(points_2d)
    print(f"\n2D layer symmetry: {final_symmetry:.3f}")


def experiment_emergent_behavior():
    """
    Experiment: Emergent behavior from simple rules.

    From the document: "when contract and expand happens in a certain
    pattern based on light input, an organism moves toward food."
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Emergent Behavior")
    print("=" * 60)

    # Simple "organism" with cells that expand/contract
    @dataclass
    class Cell:
        x: float
        y: float
        size: float = 1.0

        def sense_gradient(self, target_x: float, target_y: float) -> float:
            """Sense direction to target (like sensing light)."""
            dx = target_x - self.x
            dy = target_y - self.y
            return math.sqrt(dx**2 + dy**2)

    # Create a simple organism (3 cells in a line)
    cells = [
        Cell(40, 50),
        Cell(50, 50),
        Cell(60, 50),
    ]

    # Target (food/light source)
    target = (80, 50)

    print(f"\nTarget (food): {target}")
    print(f"Initial cell positions: {[(c.x, c.y) for c in cells]}")

    # Emergent behavior: cells closer to target expand, others contract
    # This creates movement toward target
    for step in range(20):
        # Each cell senses distance to target
        distances = [c.sense_gradient(target[0], target[1]) for c in cells]
        min_dist = min(distances)
        max_dist = max(distances)

        # Closer cells expand, farther cells contract
        for i, cell in enumerate(cells):
            if max_dist > min_dist:
                relative_dist = (distances[i] - min_dist) / (max_dist - min_dist)
                cell.size = 1.0 + (0.5 - relative_dist) * 0.5  # 0.75 to 1.25

        # Movement: centroid moves toward larger cells
        total_size = sum(c.size for c in cells)
        weighted_x = sum(c.x * c.size for c in cells) / total_size
        weighted_y = sum(c.y * c.size for c in cells) / total_size

        # Move all cells to maintain formation, shifted toward weighted center
        current_centroid_x = sum(c.x for c in cells) / len(cells)
        shift_x = (weighted_x - current_centroid_x) * 0.3

        for cell in cells:
            cell.x += shift_x

        if step % 5 == 0:
            centroid = sum(c.x for c in cells) / len(cells)
            print(f"  Step {step}: centroid at x={centroid:.1f}, distance to target: {abs(target[0]-centroid):.1f}")

    final_centroid = sum(c.x for c in cells) / len(cells)
    print(f"\nFinal cell positions: {[(f'{c.x:.1f}', f'{c.y:.1f}') for c in cells]}")
    print(f"Distance to target: {abs(target[0]-final_centroid):.1f}")
    print("\nInsight: Simple local rules (expand/contract) create global behavior (movement)")


def main():
    """Run all emergent intelligence experiments."""
    print("\n" + "=" * 70)
    print("EMERGENT INTELLIGENCE EXPERIMENTS")
    print("Exploring how intelligence arises from complexity space interactions")
    print("=" * 70)

    experiment_redundancy_creates_agency()
    experiment_patterns_as_attractors()
    experiment_cross_layer_communication()
    experiment_emergent_behavior()

    print("\n" + "=" * 70)
    print("SUMMARY OF FINDINGS")
    print("=" * 70)
    print("""
1. Redundancy Creates Agency:
   - Points with multiple specifications have OPTIONS
   - Options = degrees of freedom = ability to respond
   - "Intelligence needs redundancy to give it room to move"

2. Patterns as Attractors:
   - Patterns pull configurations toward satisfaction
   - Same pattern expressed differently at each layer
   - "Patterns come from logic, order, memory, experience"

3. Cross-Layer Communication:
   - Signals propagate between dimensional layers
   - Each layer interprets signals in its own context
   - No explicit message passing - shared substrate suffices

4. Emergent Behavior:
   - Simple local rules create complex global behavior
   - Individual cells don't "know" the goal
   - Movement emerges from differential expansion/contraction

5. Key Insight:
   Intelligence is not located in any single layer, but EMERGES
   from the negotiation between layers operating on shared substrate.
   Each layer has "agency" proportional to its redundancy and can
   influence others through the patterns it tries to satisfy.
""")


if __name__ == "__main__":
    main()
