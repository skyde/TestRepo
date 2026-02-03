"""
Complexity Spaces - Core Implementation

This module implements the theoretical framework for complexity spaces,
exploring how values exist within calibrated contexts and how multiple
perspectives can operate on shared substrates.

Key concepts:
- Values only have meaning through comparison (calibration)
- Spaces define the rules for how elements interact
- Multiple perspectives can exist simultaneously on the same elements
- Error exists in both value and frame of reference
- Intelligence emerges from negotiation between layers
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple, Callable, Dict, Any
import math
from abc import ABC, abstractmethod


class Certainty(Enum):
    """Represents the knowledge state of a value."""
    UNKNOWN = auto()    # Completely unknown
    PARTIAL = auto()    # Partially known (bounded, probabilistic)
    CERTAIN = auto()    # Fully determined


class Relation(Enum):
    """Relationships between measures in a space."""
    UNKNOWN = 0
    DUPLICATE = 1       # Same value, same location
    MIRROR = 2          # Reflection (doubles conceptual size)
    NEGATION = 4        # Opposite direction (avg to zero)
    CENTER = 8          # Downcast from higher dim (2pts -> 1pt center)
    REPEATED = 16       # Upcast (1pt -> 2pts at same logical spot)
    UNIT_DERIVED = 32   # Derived from scalar by unit application
    SIBLING = 64        # Unrelated point in shared dimension
    EXTERNAL = 128      # Point from external dimension
    DOWNCAST = 256      # Point from higher dimension projected down


@dataclass
class Measure:
    """
    A measure represents a value with its uncertainty and bounds.

    Unlike traditional real numbers that assume infinite precision,
    measures explicitly track:
    - Resolution (how precisely we know the value)
    - Bounds (what range is valid for this measure)
    - Certainty (how confident we are)
    """
    value: float
    resolution: int = 1000  # Denominator for resolution (1000 = 3 decimal places)
    min_bound: float = float('-inf')
    max_bound: float = float('inf')
    certainty: Certainty = Certainty.CERTAIN
    relation: Relation = Relation.SIBLING

    def __post_init__(self):
        # Quantize value to resolution
        self.value = round(self.value * self.resolution) / self.resolution

    @property
    def is_valid(self) -> bool:
        """Check if value is within bounds."""
        return self.min_bound <= self.value <= self.max_bound

    @property
    def validity_error(self) -> float:
        """How far outside bounds (0 if valid)."""
        if self.value < self.min_bound:
            return self.min_bound - self.value
        elif self.value > self.max_bound:
            return self.value - self.max_bound
        return 0.0

    def project_to_resolution(self, new_resolution: int) -> 'Measure':
        """Project to different resolution, losing or gaining precision."""
        new_value = round(self.value * new_resolution) / new_resolution
        return Measure(
            value=new_value,
            resolution=new_resolution,
            min_bound=self.min_bound,
            max_bound=self.max_bound,
            certainty=Certainty.PARTIAL if new_resolution < self.resolution else self.certainty
        )

    def combine(self, other: 'Measure', op: str = '+') -> 'Measure':
        """Combine two measures with an operation."""
        # Resolution becomes the minimum (information loss)
        new_res = min(self.resolution, other.resolution)

        if op == '+':
            new_val = self.value + other.value
            new_min = self.min_bound + other.min_bound
            new_max = self.max_bound + other.max_bound
        elif op == '-':
            new_val = self.value - other.value
            new_min = self.min_bound - other.max_bound
            new_max = self.max_bound - other.min_bound
        elif op == '*':
            new_val = self.value * other.value
            # Bounds get more complex with multiplication
            corners = [
                self.min_bound * other.min_bound,
                self.min_bound * other.max_bound,
                self.max_bound * other.min_bound,
                self.max_bound * other.max_bound
            ]
            new_min = min(corners)
            new_max = max(corners)
        elif op == '/':
            if other.value == 0:
                return Measure(float('nan'), certainty=Certainty.UNKNOWN)
            new_val = self.value / other.value
            # Handle division bounds carefully
            if other.min_bound <= 0 <= other.max_bound:
                new_min, new_max = float('-inf'), float('inf')
            else:
                corners = [
                    self.min_bound / other.min_bound if other.min_bound != 0 else float('inf'),
                    self.min_bound / other.max_bound if other.max_bound != 0 else float('inf'),
                    self.max_bound / other.min_bound if other.min_bound != 0 else float('inf'),
                    self.max_bound / other.max_bound if other.max_bound != 0 else float('inf')
                ]
                new_min = min(corners)
                new_max = max(corners)
        else:
            raise ValueError(f"Unknown operation: {op}")

        # Certainty degrades if either input is uncertain
        new_certainty = Certainty.PARTIAL if (
            self.certainty != Certainty.CERTAIN or
            other.certainty != Certainty.CERTAIN
        ) else Certainty.CERTAIN

        return Measure(
            value=new_val,
            resolution=new_res,
            min_bound=new_min,
            max_bound=new_max,
            certainty=new_certainty
        )

    def __repr__(self):
        bounds = f"[{self.min_bound}, {self.max_bound}]" if self.min_bound != float('-inf') or self.max_bound != float('inf') else ""
        return f"Measure({self.value}, res={self.resolution}{bounds}, {self.certainty.name})"


@dataclass
class Point:
    """
    A point in a complexity space.

    Points are the primitives of any perspective. A single point
    has no inherent value - it only gains meaning through comparison
    with other points.
    """
    measures: List[Measure] = field(default_factory=list)

    @property
    def dimensions(self) -> int:
        return len(self.measures)

    def __getitem__(self, idx: int) -> Measure:
        return self.measures[idx]

    def __repr__(self):
        if not self.measures:
            return "Point(uncharacterized)"
        coords = ", ".join(str(m.value) for m in self.measures)
        return f"Point({coords})"


@dataclass
class Segment:
    """
    A segment connects two points, creating a 1D subspace.

    The segment is the simplest structure that carries information:
    - Length (difference between endpoints)
    - Direction (which end is start vs end)
    - Position (where it exists in the containing space)
    """
    start: Point
    end: Point

    @property
    def length(self) -> float:
        """Euclidean length of the segment."""
        if self.start.dimensions != self.end.dimensions:
            raise ValueError("Points must have same dimensionality")

        squared_sum = sum(
            (e.value - s.value) ** 2
            for s, e in zip(self.start.measures, self.end.measures)
        )
        return math.sqrt(squared_sum)

    @property
    def midpoint(self) -> Point:
        """Center point of the segment."""
        mid_measures = [
            Measure(
                value=(s.value + e.value) / 2,
                resolution=min(s.resolution, e.resolution),
                certainty=Certainty.PARTIAL if s.certainty != Certainty.CERTAIN or e.certainty != Certainty.CERTAIN else Certainty.CERTAIN
            )
            for s, e in zip(self.start.measures, self.end.measures)
        ]
        return Point(mid_measures)

    @property
    def direction(self) -> List[float]:
        """Unit direction vector from start to end."""
        length = self.length
        if length == 0:
            return [0.0] * self.start.dimensions
        return [
            (e.value - s.value) / length
            for s, e in zip(self.start.measures, self.end.measures)
        ]

    def project_to_point(self) -> Point:
        """Collapse segment to its center (dimensional reduction)."""
        return self.midpoint

    def __repr__(self):
        return f"Segment({self.start} -> {self.end}, len={self.length:.3f})"


class ComplexitySpace(ABC):
    """
    Abstract base for complexity spaces.

    A complexity space defines:
    - The number of types/dimensions it contains
    - How elements interact within the space
    - The bounds and resolution of the space
    - Transformation rules between this and other spaces
    """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Number of independent dimensions in this space."""
        pass

    @property
    @abstractmethod
    def degrees_of_freedom(self) -> int:
        """Total degrees of freedom for elements in this space."""
        pass

    @abstractmethod
    def contains(self, element: Any) -> bool:
        """Check if an element is valid within this space."""
        pass

    @abstractmethod
    def project_down(self, element: Any) -> Any:
        """Project element to lower dimensional representation."""
        pass

    @abstractmethod
    def embed_up(self, element: Any) -> Any:
        """Embed element into higher dimensional representation."""
        pass


@dataclass
class LinearSpace(ComplexitySpace):
    """
    A 1D complexity space (a line).

    Points in this space have 1 degree of freedom.
    Segments have 2 degrees of freedom (each endpoint can move).
    """
    min_val: float = float('-inf')
    max_val: float = float('inf')
    resolution: int = 1000

    @property
    def dimensions(self) -> int:
        return 1

    @property
    def degrees_of_freedom(self) -> int:
        return 1  # For a point

    def contains(self, element: Any) -> bool:
        if isinstance(element, Point):
            if element.dimensions != 1:
                return False
            val = element.measures[0].value
            return self.min_val <= val <= self.max_val
        elif isinstance(element, Segment):
            return self.contains(element.start) and self.contains(element.end)
        return False

    def project_down(self, element: Any) -> Point:
        """Project to 0D (a point)."""
        if isinstance(element, Segment):
            return element.midpoint
        elif isinstance(element, Point):
            return element
        raise ValueError(f"Cannot project {type(element)}")

    def embed_up(self, element: Any) -> Segment:
        """Embed point as degenerate segment."""
        if isinstance(element, Point):
            return Segment(element, element)
        raise ValueError(f"Cannot embed {type(element)}")

    def create_point(self, value: float) -> Point:
        """Create a point in this space."""
        measure = Measure(
            value=value,
            resolution=self.resolution,
            min_bound=self.min_val,
            max_bound=self.max_val
        )
        return Point([measure])

    def create_segment(self, start: float, end: float) -> Segment:
        """Create a segment in this space."""
        return Segment(self.create_point(start), self.create_point(end))


@dataclass
class PlanarSpace(ComplexitySpace):
    """
    A 2D complexity space (a plane/area).

    Points have 2 degrees of freedom.
    Segments have 4 degrees of freedom.
    """
    x_bounds: Tuple[float, float] = (float('-inf'), float('inf'))
    y_bounds: Tuple[float, float] = (float('-inf'), float('inf'))
    resolution: int = 1000

    @property
    def dimensions(self) -> int:
        return 2

    @property
    def degrees_of_freedom(self) -> int:
        return 2  # For a point

    def contains(self, element: Any) -> bool:
        if isinstance(element, Point):
            if element.dimensions != 2:
                return False
            x, y = element.measures[0].value, element.measures[1].value
            return (self.x_bounds[0] <= x <= self.x_bounds[1] and
                    self.y_bounds[0] <= y <= self.y_bounds[1])
        elif isinstance(element, Segment):
            return self.contains(element.start) and self.contains(element.end)
        return False

    def project_down(self, element: Any) -> Any:
        """Project to 1D (collapse one dimension)."""
        if isinstance(element, Point):
            # Project to x-axis by default
            return Point([element.measures[0]])
        elif isinstance(element, Segment):
            # Project segment to line
            return Segment(
                Point([element.start.measures[0]]),
                Point([element.end.measures[0]])
            )
        raise ValueError(f"Cannot project {type(element)}")

    def embed_up(self, element: Any) -> Any:
        """Embed into 3D (add z=0)."""
        if isinstance(element, Point):
            return Point(element.measures + [Measure(0.0, self.resolution)])
        raise ValueError(f"Cannot embed {type(element)}")

    def create_point(self, x: float, y: float) -> Point:
        """Create a point in this space."""
        return Point([
            Measure(x, self.resolution, self.x_bounds[0], self.x_bounds[1]),
            Measure(y, self.resolution, self.y_bounds[0], self.y_bounds[1])
        ])

    def area_of_triangle(self, p1: Point, p2: Point, p3: Point) -> float:
        """Calculate area of triangle formed by three points."""
        # Using cross product formula
        x1, y1 = p1.measures[0].value, p1.measures[1].value
        x2, y2 = p2.measures[0].value, p2.measures[1].value
        x3, y3 = p3.measures[0].value, p3.measures[1].value

        return abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2


@dataclass
class VolumetricSpace(ComplexitySpace):
    """
    A 3D complexity space (volume).

    Points have 3 degrees of freedom.
    Segments have 6 degrees of freedom.
    """
    x_bounds: Tuple[float, float] = (float('-inf'), float('inf'))
    y_bounds: Tuple[float, float] = (float('-inf'), float('inf'))
    z_bounds: Tuple[float, float] = (float('-inf'), float('inf'))
    resolution: int = 1000

    @property
    def dimensions(self) -> int:
        return 3

    @property
    def degrees_of_freedom(self) -> int:
        return 3  # For a point

    def contains(self, element: Any) -> bool:
        if isinstance(element, Point):
            if element.dimensions != 3:
                return False
            x = element.measures[0].value
            y = element.measures[1].value
            z = element.measures[2].value
            return (self.x_bounds[0] <= x <= self.x_bounds[1] and
                    self.y_bounds[0] <= y <= self.y_bounds[1] and
                    self.z_bounds[0] <= z <= self.z_bounds[1])
        elif isinstance(element, Segment):
            return self.contains(element.start) and self.contains(element.end)
        return False

    def project_down(self, element: Any) -> Any:
        """Project to 2D (collapse z dimension)."""
        if isinstance(element, Point):
            return Point([element.measures[0], element.measures[1]])
        elif isinstance(element, Segment):
            return Segment(
                Point([element.start.measures[0], element.start.measures[1]]),
                Point([element.end.measures[0], element.end.measures[1]])
            )
        raise ValueError(f"Cannot project {type(element)}")

    def embed_up(self, element: Any) -> Any:
        """Cannot embed into 4D in this basic implementation."""
        raise NotImplementedError("4D embedding not implemented")

    def create_point(self, x: float, y: float, z: float) -> Point:
        """Create a point in this space."""
        return Point([
            Measure(x, self.resolution, self.x_bounds[0], self.x_bounds[1]),
            Measure(y, self.resolution, self.y_bounds[0], self.y_bounds[1]),
            Measure(z, self.resolution, self.z_bounds[0], self.z_bounds[1])
        ])


class Perspective:
    """
    A perspective is a view into a complexity space.

    Multiple perspectives can exist on the same elements simultaneously.
    Each perspective has its own constraints and goals, and they
    'negotiate' outcomes through the shared substrate.
    """

    def __init__(self, space: ComplexitySpace, name: str = ""):
        self.space = space
        self.name = name
        self.constraints: List[Callable[[Any], float]] = []
        self.elements: List[Any] = []
        self.desires: Dict[Any, List[float]] = {}  # Element -> desired adjustments

    def add_constraint(self, constraint: Callable[[Any], float]):
        """
        Add a constraint function that returns error magnitude.
        0 = constraint satisfied, >0 = how far from satisfaction.
        """
        self.constraints.append(constraint)

    def add_element(self, element: Any):
        """Add an element to this perspective."""
        if self.space.contains(element):
            self.elements.append(element)
            self.desires[id(element)] = [0.0] * self.space.dimensions
        else:
            raise ValueError(f"Element not valid in space: {element}")

    def compute_error(self, element: Any) -> float:
        """Compute total constraint violation for an element."""
        return sum(c(element) for c in self.constraints)

    def compute_total_error(self) -> float:
        """Compute total error across all elements."""
        return sum(self.compute_error(e) for e in self.elements)

    def express_desire(self, element: Any, adjustments: List[float]):
        """Express a desire for an element to move."""
        self.desires[id(element)] = adjustments

    def __repr__(self):
        return f"Perspective({self.name}, {len(self.elements)} elements)"


class MultiPerspectiveSystem:
    """
    A system where multiple perspectives operate on shared elements.

    This implements the key insight from the document: perspectives
    communicate automatically through the shared substrate, without
    explicit message passing.
    """

    def __init__(self):
        self.perspectives: List[Perspective] = []
        self.shared_elements: List[Any] = []

    def add_perspective(self, perspective: Perspective):
        """Add a perspective to the system."""
        self.perspectives.append(perspective)

    def add_shared_element(self, element: Any):
        """Add an element shared across perspectives."""
        self.shared_elements.append(element)
        for p in self.perspectives:
            if p.space.contains(element):
                p.add_element(element)

    def negotiate_step(self, learning_rate: float = 0.1) -> float:
        """
        Perform one step of negotiation between perspectives.

        Each perspective expresses its desires, and elements
        move toward the weighted average of all desires.

        Returns total system error.
        """
        total_error = 0.0

        for element in self.shared_elements:
            if isinstance(element, Point):
                # Collect desires from all perspectives containing this element
                all_desires = []
                all_weights = []

                for p in self.perspectives:
                    if p.space.contains(element):
                        error = p.compute_error(element)
                        total_error += error

                        # Compute gradient-like desire (move away from error)
                        desires = p.desires.get(id(element), [0.0] * element.dimensions)
                        all_desires.append(desires)
                        all_weights.append(1.0 / (error + 0.001))  # Weight by inverse error

                if all_desires:
                    # Weighted average of desires
                    total_weight = sum(all_weights)
                    for dim in range(element.dimensions):
                        weighted_desire = sum(
                            d[dim] * w for d, w in zip(all_desires, all_weights)
                        ) / total_weight

                        # Apply adjustment
                        element.measures[dim].value += learning_rate * weighted_desire

        return total_error

    def negotiate(self, max_iterations: int = 100, tolerance: float = 0.001) -> int:
        """
        Negotiate until convergence or max iterations.
        Returns number of iterations taken.
        """
        for i in range(max_iterations):
            error = self.negotiate_step()
            if error < tolerance:
                return i + 1
        return max_iterations


# Number systems as complexity spaces

@dataclass
class RationalNumber:
    """
    A rational number as two measures (numerator and denominator).

    This keeps the components unconsolidated, preserving calibration
    information and allowing tracking of projection scales.
    """
    numerator: Measure
    denominator: Measure

    @property
    def value(self) -> float:
        if self.denominator.value == 0:
            return float('nan')
        return self.numerator.value / self.denominator.value

    def __add__(self, other: 'RationalNumber') -> 'RationalNumber':
        # a/b + c/d = (ad + bc) / bd
        new_num = self.numerator.combine(other.denominator, '*').combine(
            other.numerator.combine(self.denominator, '*'), '+'
        )
        new_denom = self.denominator.combine(other.denominator, '*')
        return RationalNumber(new_num, new_denom)

    def __mul__(self, other: 'RationalNumber') -> 'RationalNumber':
        # a/b * c/d = ac / bd
        new_num = self.numerator.combine(other.numerator, '*')
        new_denom = self.denominator.combine(other.denominator, '*')
        return RationalNumber(new_num, new_denom)

    def __repr__(self):
        return f"Rational({self.numerator.value}/{self.denominator.value} = {self.value:.4f})"


@dataclass
class ComplexNumber:
    """
    A complex number as four unconsolidated measures.

    Represents (a + bi) where:
    - real_num/real_denom = a
    - imag_num/imag_denom = b
    """
    real_num: Measure
    real_denom: Measure
    imag_num: Measure
    imag_denom: Measure

    @property
    def real(self) -> float:
        return self.real_num.value / self.real_denom.value

    @property
    def imag(self) -> float:
        return self.imag_num.value / self.imag_denom.value

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.real ** 2 + self.imag ** 2)

    @property
    def phase(self) -> float:
        return math.atan2(self.imag, self.real)

    def __add__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        # (a+bi) + (c+di) = (a+c) + (b+d)i
        # Need to add rationals properly
        r1 = RationalNumber(self.real_num, self.real_denom)
        r2 = RationalNumber(other.real_num, other.real_denom)
        i1 = RationalNumber(self.imag_num, self.imag_denom)
        i2 = RationalNumber(other.imag_num, other.imag_denom)

        real_sum = r1 + r2
        imag_sum = i1 + i2

        return ComplexNumber(
            real_sum.numerator, real_sum.denominator,
            imag_sum.numerator, imag_sum.denominator
        )

    def __mul__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        # (a+bi)(c+di) = (ac-bd) + (ad+bc)i
        a, b = self.real, self.imag
        c, d = other.real, other.imag

        real_part = a*c - b*d
        imag_part = a*d + b*c

        return ComplexNumber(
            Measure(real_part), Measure(1.0),
            Measure(imag_part), Measure(1.0)
        )

    def __repr__(self):
        sign = '+' if self.imag >= 0 else ''
        return f"Complex({self.real:.4f}{sign}{self.imag:.4f}i)"


if __name__ == "__main__":
    # Basic demonstration
    print("=== Complexity Spaces Core Module ===\n")

    # Create a linear space
    line = LinearSpace(min_val=0, max_val=10)
    p1 = line.create_point(3.0)
    p2 = line.create_point(7.0)
    seg = Segment(p1, p2)

    print(f"Linear space: {line}")
    print(f"Point 1: {p1}")
    print(f"Point 2: {p2}")
    print(f"Segment: {seg}")
    print(f"Midpoint: {seg.midpoint}")
    print()

    # Create a planar space
    plane = PlanarSpace(x_bounds=(0, 10), y_bounds=(0, 10))
    p3 = plane.create_point(2.0, 3.0)
    p4 = plane.create_point(8.0, 7.0)

    print(f"Planar space: {plane}")
    print(f"Point 3: {p3}")
    print(f"Point 4: {p4}")
    print(f"Contains p3: {plane.contains(p3)}")
    print()

    # Demonstrate rational numbers
    r1 = RationalNumber(Measure(3), Measure(4))
    r2 = RationalNumber(Measure(1), Measure(2))
    print(f"Rational 1: {r1}")
    print(f"Rational 2: {r2}")
    print(f"Sum: {r1 + r2}")
    print(f"Product: {r1 * r2}")
    print()

    # Demonstrate complex numbers
    c1 = ComplexNumber(Measure(3), Measure(1), Measure(4), Measure(1))
    c2 = ComplexNumber(Measure(1), Measure(1), Measure(2), Measure(1))
    print(f"Complex 1: {c1}")
    print(f"Complex 2: {c2}")
    print(f"Sum: {c1 + c2}")
    print(f"Product: {c1 * c2}")
