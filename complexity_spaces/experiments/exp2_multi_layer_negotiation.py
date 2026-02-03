"""
Experiment 2: Multi-Layer Communication and Negotiation

This experiment explores the key insight from the document:
"The beauty of multiple parallel perspectives is that the communication
happens automatically. This happens because all the independent layers
operate on the same substrate."

We model:
1. Multiple perspectives with different goals
2. Automatic negotiation through shared substrate
3. Emergence of stable configurations
"""

import sys
sys.path.insert(0, '/home/user/TestRepo/complexity_spaces')

from core import (
    Measure, Point, Segment, Certainty,
    LinearSpace, PlanarSpace, Perspective, MultiPerspectiveSystem
)
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Callable, Dict
import random


@dataclass
class Force:
    """A force acting on a point in a specific direction."""
    point_id: int
    direction: List[float]
    magnitude: float
    source: str  # Which layer/perspective generated this force


@dataclass
class NegotiatingPoint:
    """
    A point that can receive forces from multiple perspectives
    and negotiate its position.
    """
    position: List[float]
    forces: List[Force] = field(default_factory=list)
    history: List[List[float]] = field(default_factory=list)

    def apply_forces(self, learning_rate: float = 0.1) -> float:
        """
        Apply all forces and move toward equilibrium.
        Returns total movement magnitude.
        """
        if not self.forces:
            return 0.0

        # Sum all forces (weighted by magnitude)
        total_force = [0.0] * len(self.position)
        total_weight = 0.0

        for f in self.forces:
            for i, d in enumerate(f.direction):
                total_force[i] += d * f.magnitude
            total_weight += f.magnitude

        if total_weight > 0:
            total_force = [f / total_weight for f in total_force]

        # Apply movement
        movement = 0.0
        for i in range(len(self.position)):
            delta = learning_rate * total_force[i]
            self.position[i] += delta
            movement += delta ** 2

        self.history.append(list(self.position))
        self.forces.clear()

        return math.sqrt(movement)


class GeometricPerspective:
    """
    A perspective that wants points to form a specific geometric shape.
    """

    def __init__(self, name: str, target_shape: str, points: List[NegotiatingPoint]):
        self.name = name
        self.target_shape = target_shape
        self.points = points

    def compute_forces(self) -> List[Force]:
        """Compute forces based on desired shape."""
        forces = []

        if self.target_shape == "line":
            # Want all points on a line (minimize perpendicular distance)
            forces.extend(self._line_forces())
        elif self.target_shape == "circle":
            # Want all points equidistant from center
            forces.extend(self._circle_forces())
        elif self.target_shape == "spread":
            # Want points maximally spread apart
            forces.extend(self._spread_forces())
        elif self.target_shape == "cluster":
            # Want points close together
            forces.extend(self._cluster_forces())

        return forces

    def _line_forces(self) -> List[Force]:
        """Push points toward a best-fit line."""
        if len(self.points) < 2:
            return []

        # Calculate centroid
        cx = sum(p.position[0] for p in self.points) / len(self.points)
        cy = sum(p.position[1] for p in self.points) / len(self.points)

        # Find principal axis (direction of maximum variance)
        # Simplified: use first two points to define line direction
        if len(self.points) >= 2:
            dx = self.points[1].position[0] - self.points[0].position[0]
            dy = self.points[1].position[1] - self.points[0].position[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx, dy = dx/length, dy/length
            else:
                dx, dy = 1.0, 0.0
        else:
            dx, dy = 1.0, 0.0

        forces = []
        for i, p in enumerate(self.points):
            # Project point onto line and compute perpendicular push
            px, py = p.position[0] - cx, p.position[1] - cy
            proj_length = px * dx + py * dy
            proj_x, proj_y = proj_length * dx, proj_length * dy

            # Perpendicular component (what needs to be corrected)
            perp_x = px - proj_x
            perp_y = py - proj_y
            perp_dist = math.sqrt(perp_x**2 + perp_y**2)

            if perp_dist > 0.001:
                forces.append(Force(
                    point_id=i,
                    direction=[-perp_x/perp_dist, -perp_y/perp_dist],
                    magnitude=perp_dist,
                    source=f"{self.name}:line"
                ))

        return forces

    def _circle_forces(self) -> List[Force]:
        """Push points toward a circle around centroid."""
        if len(self.points) < 2:
            return []

        # Calculate centroid
        cx = sum(p.position[0] for p in self.points) / len(self.points)
        cy = sum(p.position[1] for p in self.points) / len(self.points)

        # Calculate average distance (target radius)
        avg_dist = sum(
            math.sqrt((p.position[0]-cx)**2 + (p.position[1]-cy)**2)
            for p in self.points
        ) / len(self.points)

        forces = []
        for i, p in enumerate(self.points):
            dx = p.position[0] - cx
            dy = p.position[1] - cy
            dist = math.sqrt(dx**2 + dy**2)

            if dist > 0.001:
                # Push toward/away from center to match avg_dist
                error = avg_dist - dist
                direction = [dx/dist, dy/dist]
                forces.append(Force(
                    point_id=i,
                    direction=direction,
                    magnitude=abs(error),
                    source=f"{self.name}:circle"
                ))

        return forces

    def _spread_forces(self) -> List[Force]:
        """Push points apart (maximize spacing)."""
        forces = []
        for i, p1 in enumerate(self.points):
            for j, p2 in enumerate(self.points):
                if i >= j:
                    continue

                dx = p1.position[0] - p2.position[0]
                dy = p1.position[1] - p2.position[1]
                dist = math.sqrt(dx**2 + dy**2)

                if dist < 0.001:
                    dist = 0.001
                    dx, dy = random.random(), random.random()

                # Repulsive force inversely proportional to distance
                force_mag = 10.0 / (dist + 1)
                direction = [dx/dist, dy/dist]

                forces.append(Force(
                    point_id=i,
                    direction=direction,
                    magnitude=force_mag,
                    source=f"{self.name}:spread"
                ))
                forces.append(Force(
                    point_id=j,
                    direction=[-direction[0], -direction[1]],
                    magnitude=force_mag,
                    source=f"{self.name}:spread"
                ))

        return forces

    def _cluster_forces(self) -> List[Force]:
        """Pull points toward centroid."""
        if len(self.points) < 2:
            return []

        cx = sum(p.position[0] for p in self.points) / len(self.points)
        cy = sum(p.position[1] for p in self.points) / len(self.points)

        forces = []
        for i, p in enumerate(self.points):
            dx = cx - p.position[0]
            dy = cy - p.position[1]
            dist = math.sqrt(dx**2 + dy**2)

            if dist > 0.001:
                forces.append(Force(
                    point_id=i,
                    direction=[dx/dist, dy/dist],
                    magnitude=dist,
                    source=f"{self.name}:cluster"
                ))

        return forces

    def compute_error(self) -> float:
        """Compute how far from target shape."""
        forces = self.compute_forces()
        return sum(f.magnitude for f in forces)


class NegotiationSystem:
    """
    A system where multiple perspectives negotiate point positions.
    """

    def __init__(self):
        self.points: List[NegotiatingPoint] = []
        self.perspectives: List[GeometricPerspective] = []
        self.error_history: List[Dict[str, float]] = []

    def add_point(self, x: float, y: float) -> NegotiatingPoint:
        """Add a point to the system."""
        point = NegotiatingPoint(position=[x, y])
        self.points.append(point)
        return point

    def add_perspective(self, perspective: GeometricPerspective):
        """Add a perspective to the system."""
        self.perspectives.append(perspective)

    def step(self, learning_rate: float = 0.1) -> Dict[str, float]:
        """
        Perform one negotiation step.
        Returns errors for each perspective.
        """
        # Collect forces from all perspectives
        all_forces: Dict[int, List[Force]] = {i: [] for i in range(len(self.points))}

        for persp in self.perspectives:
            forces = persp.compute_forces()
            for f in forces:
                all_forces[f.point_id].append(f)

        # Apply forces to each point
        for i, point in enumerate(self.points):
            point.forces = all_forces[i]
            point.apply_forces(learning_rate)

        # Compute errors
        errors = {p.name: p.compute_error() for p in self.perspectives}
        self.error_history.append(errors)

        return errors

    def negotiate(self, max_steps: int = 100, tolerance: float = 0.01,
                  learning_rate: float = 0.1) -> int:
        """
        Run negotiation until convergence.
        Returns number of steps taken.
        """
        for step in range(max_steps):
            errors = self.step(learning_rate)
            total_error = sum(errors.values())

            if total_error < tolerance:
                return step + 1

        return max_steps


def experiment_cooperative_perspectives():
    """
    Experiment: Two perspectives that want compatible things.
    Circle + Spread = evenly distributed circle
    """
    print("=" * 60)
    print("EXPERIMENT: Cooperative Perspectives")
    print("(Circle + Spread = evenly distributed circle)")
    print("=" * 60)

    system = NegotiationSystem()

    # Create random initial points
    random.seed(42)
    for _ in range(6):
        x = random.uniform(20, 80)
        y = random.uniform(20, 80)
        system.add_point(x, y)

    print(f"\nInitial positions:")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    # Add cooperative perspectives
    circle_persp = GeometricPerspective("circle", "circle", system.points)
    spread_persp = GeometricPerspective("spread", "spread", system.points)

    system.add_perspective(circle_persp)
    system.add_perspective(spread_persp)

    # Run negotiation
    steps = system.negotiate(max_steps=200, tolerance=0.1, learning_rate=0.05)

    print(f"\nConverged after {steps} steps")
    print(f"\nFinal positions:")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    # Analyze result
    cx = sum(p.position[0] for p in system.points) / len(system.points)
    cy = sum(p.position[1] for p in system.points) / len(system.points)
    distances = [
        math.sqrt((p.position[0]-cx)**2 + (p.position[1]-cy)**2)
        for p in system.points
    ]
    avg_dist = sum(distances) / len(distances)
    dist_variance = sum((d - avg_dist)**2 for d in distances) / len(distances)

    print(f"\nResult Analysis:")
    print(f"  Center: ({cx:.2f}, {cy:.2f})")
    print(f"  Average radius: {avg_dist:.2f}")
    print(f"  Radius variance: {dist_variance:.4f} (lower = more circular)")

    # Check spacing
    min_spacing = float('inf')
    for i, p1 in enumerate(system.points):
        for j, p2 in enumerate(system.points):
            if i < j:
                d = math.sqrt((p1.position[0]-p2.position[0])**2 +
                            (p1.position[1]-p2.position[1])**2)
                min_spacing = min(min_spacing, d)

    print(f"  Minimum spacing: {min_spacing:.2f} (higher = better spread)")


def experiment_competing_perspectives():
    """
    Experiment: Two perspectives that want incompatible things.
    Line + Circle = compromise shape
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Competing Perspectives")
    print("(Line + Circle = compromise shape)")
    print("=" * 60)

    system = NegotiationSystem()

    # Create points in a line initially
    for i in range(5):
        x = 20 + i * 15
        y = 50
        system.add_point(x, y)

    print(f"\nInitial positions (on a line):")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    # Add competing perspectives
    line_persp = GeometricPerspective("line", "line", system.points)
    circle_persp = GeometricPerspective("circle", "circle", system.points)

    system.add_perspective(line_persp)
    system.add_perspective(circle_persp)

    # Run negotiation
    steps = system.negotiate(max_steps=200, tolerance=0.5, learning_rate=0.03)

    print(f"\nNegotiated for {steps} steps")
    print(f"\nFinal positions:")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    final_errors = system.error_history[-1]
    print(f"\nFinal errors:")
    print(f"  Line perspective: {final_errors['line']:.2f}")
    print(f"  Circle perspective: {final_errors['circle']:.2f}")
    print(f"\nInsight: Neither perspective fully satisfied, but both partially accommodated")


def experiment_weighted_perspectives():
    """
    Experiment: Same perspectives but with different weights/importance.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Weighted Perspectives")
    print("(Same goals, different importance)")
    print("=" * 60)

    # Run twice with different weight configurations

    for config_name, cluster_weight, spread_weight in [
        ("Strong Cluster", 5.0, 1.0),
        ("Strong Spread", 1.0, 5.0)
    ]:
        print(f"\n--- {config_name} ---")

        system = NegotiationSystem()

        random.seed(123)
        for _ in range(5):
            x = random.uniform(30, 70)
            y = random.uniform(30, 70)
            system.add_point(x, y)

        # Create weighted perspectives by adjusting force magnitudes
        class WeightedPerspective(GeometricPerspective):
            def __init__(self, name, shape, points, weight):
                super().__init__(name, shape, points)
                self.weight = weight

            def compute_forces(self):
                forces = super().compute_forces()
                for f in forces:
                    f.magnitude *= self.weight
                return forces

        cluster_persp = WeightedPerspective("cluster", "cluster", system.points, cluster_weight)
        spread_persp = WeightedPerspective("spread", "spread", system.points, spread_weight)

        system.add_perspective(cluster_persp)
        system.add_perspective(spread_persp)

        steps = system.negotiate(max_steps=100, tolerance=0.1, learning_rate=0.05)

        # Measure final spread
        cx = sum(p.position[0] for p in system.points) / len(system.points)
        cy = sum(p.position[1] for p in system.points) / len(system.points)
        avg_dist = sum(
            math.sqrt((p.position[0]-cx)**2 + (p.position[1]-cy)**2)
            for p in system.points
        ) / len(system.points)

        print(f"  Average distance from center: {avg_dist:.2f}")
        print(f"  (Higher distance = spread won, Lower = cluster won)")


def experiment_emergent_structure():
    """
    Experiment: Multiple layers creating emergent structure.

    Simulates: Points -> Segments -> Area
    Each layer has its own goals that combine to create emergent form.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Emergent Multi-Layer Structure")
    print("(Points, Segments, and Area perspectives)")
    print("=" * 60)

    system = NegotiationSystem()

    # Create a triangle of points
    points = []
    for angle in [0, 120, 240]:
        rad = math.radians(angle)
        x = 50 + 30 * math.cos(rad)
        y = 50 + 30 * math.sin(rad)
        p = system.add_point(x, y)
        points.append(p)

    print(f"\nInitial triangle:")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    # Layer 1: Points want to be spread
    point_persp = GeometricPerspective("points", "spread", system.points)

    # Layer 2: Imagine edges want equal length (implicit through circle)
    edge_persp = GeometricPerspective("edges", "circle", system.points)

    # Layer 3: Area wants to be centered at (50, 50)
    class CenteredAreaPerspective(GeometricPerspective):
        def __init__(self, name, points, target_center):
            super().__init__(name, "cluster", points)
            self.target_center = target_center

        def compute_forces(self):
            # Push entire shape toward target center
            cx = sum(p.position[0] for p in self.points) / len(self.points)
            cy = sum(p.position[1] for p in self.points) / len(self.points)

            dx = self.target_center[0] - cx
            dy = self.target_center[1] - cy
            dist = math.sqrt(dx**2 + dy**2)

            forces = []
            if dist > 0.001:
                direction = [dx/dist, dy/dist]
                for i, p in enumerate(self.points):
                    forces.append(Force(
                        point_id=i,
                        direction=direction,
                        magnitude=dist * 0.5,
                        source=f"{self.name}:center"
                    ))
            return forces

    area_persp = CenteredAreaPerspective("area", system.points, (50, 50))

    system.add_perspective(point_persp)
    system.add_perspective(edge_persp)
    system.add_perspective(area_persp)

    # Perturb one point
    system.points[0].position[0] += 20
    system.points[0].position[1] += 10

    print(f"\nAfter perturbation:")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    # Let system negotiate
    steps = system.negotiate(max_steps=150, tolerance=0.5, learning_rate=0.03)

    print(f"\nNegotiated for {steps} steps")
    print(f"\nFinal positions:")
    for i, p in enumerate(system.points):
        print(f"  Point {i}: ({p.position[0]:.2f}, {p.position[1]:.2f})")

    # Analyze emergence
    cx = sum(p.position[0] for p in system.points) / len(system.points)
    cy = sum(p.position[1] for p in system.points) / len(system.points)
    print(f"\nEmergent Properties:")
    print(f"  Center: ({cx:.2f}, {cy:.2f}) (target: 50, 50)")

    # Check edge lengths
    edges = []
    for i in range(3):
        j = (i + 1) % 3
        dx = system.points[i].position[0] - system.points[j].position[0]
        dy = system.points[i].position[1] - system.points[j].position[1]
        edges.append(math.sqrt(dx**2 + dy**2))

    print(f"  Edge lengths: {[f'{e:.2f}' for e in edges]}")
    edge_variance = sum((e - sum(edges)/3)**2 for e in edges) / 3
    print(f"  Edge variance: {edge_variance:.4f} (lower = more equilateral)")


def main():
    """Run all negotiation experiments."""
    print("\n" + "=" * 70)
    print("MULTI-LAYER NEGOTIATION EXPERIMENTS")
    print("Exploring how perspectives communicate through shared substrate")
    print("=" * 70)

    experiment_cooperative_perspectives()
    experiment_competing_perspectives()
    experiment_weighted_perspectives()
    experiment_emergent_structure()

    print("\n" + "=" * 70)
    print("SUMMARY OF FINDINGS")
    print("=" * 70)
    print("""
1. Automatic Communication:
   - Perspectives communicate through forces on shared elements
   - No explicit message passing needed
   - Resolution happens through iterative negotiation

2. Cooperative vs Competing:
   - Cooperative perspectives (circle + spread) enhance each other
   - Competing perspectives (line + circle) find compromise
   - The result is "negotiated" not "dictated"

3. Weight Determines Influence:
   - Relative importance affects final configuration
   - Strongly weighted perspectives dominate outcome
   - But all perspectives still have some influence

4. Emergent Structure:
   - Multi-layer systems create emergent properties
   - Individual layers don't need to understand the whole
   - Stable configurations emerge from local negotiations

5. Key Insight:
   "These affect each other, and all points move...
    The communication here happens because they are all
    perspectives in the same space."
""")


if __name__ == "__main__":
    main()
