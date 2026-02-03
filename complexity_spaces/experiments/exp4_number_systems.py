"""
Experiment 4: Number Systems as Complexity Spaces

This experiment completes the "2 points" section from the document
and explores how number systems emerge from the structure of spaces.

From the document:
"1 point - Single datapoints are the primitives of any perspective"
"2 points - [Notes section incomplete]"

Key insight: Number systems are algebraic expressions that define
how values interact within a space. Different number systems
(naturals, rationals, complex, quaternions) represent different
complexity spaces.
"""

import sys
sys.path.insert(0, '/home/user/TestRepo/complexity_spaces')

from core import Measure, Point, Segment
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable
from abc import ABC, abstractmethod


# ============================================================================
# BUILDING UP FROM PRIMITIVES
# ============================================================================

@dataclass
class OnePoint:
    """
    1 Point: The absolute primitive.

    From the document: "A single primitive, regardless how it exists
    in the greater reality, can not have any value attached to it
    without having something else to calibrate it."

    A single point is valid, but uncharacterized. It is working
    material, not information.
    """
    exists: bool = True

    def __repr__(self):
        return "Point(•)" if self.exists else "Point(∅)"

    @property
    def can_measure(self) -> bool:
        """Cannot measure without comparison."""
        return False

    @property
    def degrees_of_freedom(self) -> int:
        """No movement possible without reference."""
        return 0


@dataclass
class TwoPoints:
    """
    2 Points: The first structure with measurable properties.

    Two points create:
    - A sense of "between" (ordering)
    - A length/distance (magnitude)
    - A direction (from one to other)

    This is the birth of measurement.
    """
    p1: OnePoint
    p2: OnePoint
    _distance: float = 1.0  # Arbitrary until calibrated

    @property
    def exists(self) -> bool:
        return self.p1.exists and self.p2.exists

    @property
    def can_measure(self) -> bool:
        """Can now measure by comparison."""
        return self.p1.exists and self.p2.exists

    @property
    def degrees_of_freedom(self) -> int:
        """Each point can move, so 2 DOF."""
        return 2

    def __repr__(self):
        return f"TwoPoints(• --- • distance={self._distance})"


@dataclass
class Ratio:
    """
    A ratio created by comparing two two-point structures.

    From the document: "a ratio (numerator/denominator) can only
    multiply when projected as there is a unit and things need to align."

    The ratio is our first NUMBER SYSTEM:
    - Numerator: what we're measuring
    - Denominator: the unit of measurement
    """
    numerator: TwoPoints
    denominator: TwoPoints

    @property
    def value(self) -> float:
        if self.denominator._distance == 0:
            return float('inf')
        return self.numerator._distance / self.denominator._distance

    def __repr__(self):
        return f"Ratio({self.numerator._distance}/{self.denominator._distance} = {self.value:.4f})"

    def __add__(self, other: 'Ratio') -> 'Ratio':
        """
        Addition requires common denominator.
        This is why "you can only add with identical unit types."
        """
        # a/b + c/d = (ad + bc) / bd
        new_num_dist = (self.numerator._distance * other.denominator._distance +
                       other.numerator._distance * self.denominator._distance)
        new_denom_dist = self.denominator._distance * other.denominator._distance

        return Ratio(
            TwoPoints(OnePoint(), OnePoint(), new_num_dist),
            TwoPoints(OnePoint(), OnePoint(), new_denom_dist)
        )

    def __mul__(self, other: 'Ratio') -> 'Ratio':
        """
        Multiplication combines numerators and denominators.
        This changes the TYPE (dimension) of the result.
        """
        new_num_dist = self.numerator._distance * other.numerator._distance
        new_denom_dist = self.denominator._distance * other.denominator._distance

        return Ratio(
            TwoPoints(OnePoint(), OnePoint(), new_num_dist),
            TwoPoints(OnePoint(), OnePoint(), new_denom_dist)
        )


# ============================================================================
# NUMBER SYSTEM HIERARCHY
# ============================================================================

class NumberSystem(ABC):
    """Base class for number systems as complexity spaces."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Number of independent components."""
        pass

    @property
    @abstractmethod
    def points_required(self) -> int:
        """Minimum points to define this system."""
        pass

    @abstractmethod
    def __add__(self, other):
        pass

    @abstractmethod
    def __mul__(self, other):
        pass


@dataclass
class Natural:
    """
    Natural numbers: Counting (repeated units).

    From the document: "3m is an 'm' unit repeated 3 times (add)"
    """
    count: int

    @property
    def dimension(self) -> int:
        return 1  # Scalar

    @property
    def points_required(self) -> int:
        return 2  # Need unit to count

    def __add__(self, other: 'Natural') -> 'Natural':
        return Natural(self.count + other.count)

    def __mul__(self, other: 'Natural') -> 'Natural':
        return Natural(self.count * other.count)

    def __repr__(self):
        return f"Natural({self.count})"


@dataclass
class Rational:
    """
    Rational numbers: Two naturals in ratio (numerator/denominator).

    From the document: "Number systems need to be algebraic expressions
    that are not composable, otherwise they lose their meaning."
    """
    numerator: int
    denominator: int = 1

    def __post_init__(self):
        # Keep in lowest terms
        g = math.gcd(abs(self.numerator), abs(self.denominator))
        if g > 0:
            self.numerator //= g
            self.denominator //= g
        if self.denominator < 0:
            self.numerator = -self.numerator
            self.denominator = -self.denominator

    @property
    def dimension(self) -> int:
        return 1  # Still scalar, but with precision

    @property
    def points_required(self) -> int:
        return 4  # Two segments (num and denom)

    @property
    def value(self) -> float:
        return self.numerator / self.denominator if self.denominator != 0 else float('nan')

    def __add__(self, other: 'Rational') -> 'Rational':
        new_num = self.numerator * other.denominator + other.numerator * self.denominator
        new_denom = self.denominator * other.denominator
        return Rational(new_num, new_denom)

    def __mul__(self, other: 'Rational') -> 'Rational':
        return Rational(
            self.numerator * other.numerator,
            self.denominator * other.denominator
        )

    def __repr__(self):
        if self.denominator == 1:
            return f"Rational({self.numerator})"
        return f"Rational({self.numerator}/{self.denominator})"


@dataclass
class Complex:
    """
    Complex numbers: 4 points creating 2D algebraic space.

    From the document: "Complex numbers are 4 unconsolidated types.
    All the math is done without ever combining them."
    """
    real: Rational
    imag: Rational

    @property
    def dimension(self) -> int:
        return 2  # Two independent components

    @property
    def points_required(self) -> int:
        return 8  # Two rationals, each needs 4 points

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.real.value ** 2 + self.imag.value ** 2)

    @property
    def phase(self) -> float:
        return math.atan2(self.imag.value, self.real.value)

    def __add__(self, other: 'Complex') -> 'Complex':
        return Complex(
            self.real + other.real,
            self.imag + other.imag
        )

    def __mul__(self, other: 'Complex') -> 'Complex':
        # (a+bi)(c+di) = (ac-bd) + (ad+bc)i
        a, b = self.real, self.imag
        c, d = other.real, other.imag

        real_part = a * c + Rational(-1) * b * d
        imag_part = a * d + b * c

        return Complex(real_part, imag_part)

    def __repr__(self):
        sign = '+' if self.imag.value >= 0 else ''
        return f"Complex({self.real.value:.2f}{sign}{self.imag.value:.2f}i)"


@dataclass
class Quaternion:
    """
    Quaternions: 8 components, useful for rotations in 3D.

    Following the pattern: each level doubles the point count.
    """
    w: Rational  # Scalar part
    x: Rational  # i component
    y: Rational  # j component
    z: Rational  # k component

    @property
    def dimension(self) -> int:
        return 4

    @property
    def points_required(self) -> int:
        return 16  # Four rationals

    @property
    def magnitude(self) -> float:
        return math.sqrt(
            self.w.value ** 2 + self.x.value ** 2 +
            self.y.value ** 2 + self.z.value ** 2
        )

    def __add__(self, other: 'Quaternion') -> 'Quaternion':
        return Quaternion(
            self.w + other.w,
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __mul__(self, other: 'Quaternion') -> 'Quaternion':
        # Quaternion multiplication (non-commutative)
        w = (self.w * other.w + Rational(-1) * self.x * other.x +
             Rational(-1) * self.y * other.y + Rational(-1) * self.z * other.z)
        x = (self.w * other.x + self.x * other.w +
             self.y * other.z + Rational(-1) * self.z * other.y)
        y = (self.w * other.y + Rational(-1) * self.x * other.z +
             self.y * other.w + self.z * other.x)
        z = (self.w * other.z + self.x * other.y +
             Rational(-1) * self.y * other.x + self.z * other.w)

        return Quaternion(w, x, y, z)

    def __repr__(self):
        return f"Quaternion({self.w.value:.2f} + {self.x.value:.2f}i + {self.y.value:.2f}j + {self.z.value:.2f}k)"


# ============================================================================
# EXPERIMENTS
# ============================================================================

def experiment_building_from_one_point():
    """
    Experiment: Build up number systems from the primitive point.
    """
    print("=" * 60)
    print("EXPERIMENT: Building Number Systems from Points")
    print("=" * 60)

    # Level 0: One point
    p = OnePoint()
    print(f"\n1 Point: {p}")
    print(f"  Can measure: {p.can_measure}")
    print(f"  Degrees of freedom: {p.degrees_of_freedom}")
    print(f"  -> A point alone is 'valid but uncharacterized'")

    # Level 1: Two points
    two_pts = TwoPoints(OnePoint(), OnePoint(), _distance=5.0)
    print(f"\n2 Points: {two_pts}")
    print(f"  Can measure: {two_pts.can_measure}")
    print(f"  Degrees of freedom: {two_pts.degrees_of_freedom}")
    print(f"  -> Creates: length, direction, ordering")

    # Level 2: Ratio (4 points)
    unit = TwoPoints(OnePoint(), OnePoint(), _distance=1.0)
    measured = TwoPoints(OnePoint(), OnePoint(), _distance=3.5)
    ratio = Ratio(measured, unit)
    print(f"\n4 Points (Ratio): {ratio}")
    print(f"  -> Creates: calibrated measurement")

    # Level 3: Complex (8 points)
    c = Complex(Rational(3), Rational(4))
    print(f"\n8 Points (Complex): {c}")
    print(f"  Magnitude: {c.magnitude}")
    print(f"  Phase: {math.degrees(c.phase):.1f}°")
    print(f"  -> Creates: 2D algebraic space, rotations")

    # Level 4: Quaternion (16 points)
    q = Quaternion(Rational(1), Rational(0), Rational(1), Rational(0))
    print(f"\n16 Points (Quaternion): {q}")
    print(f"  Magnitude: {q.magnitude:.3f}")
    print(f"  -> Creates: 3D rotations, orientation")


def experiment_operations_emerge_from_structure():
    """
    Experiment: Operations emerge from how points can combine.

    From the document: "All operations are inherent in the space"
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Operations Emerge from Structure")
    print("=" * 60)

    print("\n--- Addition: Combining SAME types ---")
    # Two segments tip-to-tail
    r1 = Ratio(TwoPoints(OnePoint(), OnePoint(), 3.0),
               TwoPoints(OnePoint(), OnePoint(), 1.0))
    r2 = Ratio(TwoPoints(OnePoint(), OnePoint(), 4.0),
               TwoPoints(OnePoint(), OnePoint(), 1.0))

    print(f"Segment 1: {r1}")
    print(f"Segment 2: {r2}")
    print(f"Combined (addition): {r1 + r2}")
    print("  -> Addition aligns endpoints, extends length")

    print("\n--- Multiplication: Combining DIFFERENT types ---")
    # Length × Width = Area
    length = Ratio(TwoPoints(OnePoint(), OnePoint(), 3.0),
                   TwoPoints(OnePoint(), OnePoint(), 1.0))
    width = Ratio(TwoPoints(OnePoint(), OnePoint(), 4.0),
                  TwoPoints(OnePoint(), OnePoint(), 1.0))

    print(f"Length: {length}")
    print(f"Width: {width}")
    print(f"Product (area): {length * width}")
    print("  -> Multiplication creates new dimension (area)")

    print("\n--- Complex multiplication creates rotation ---")
    # 45° rotation
    c1 = Complex(Rational(1), Rational(1))  # 45° from real axis
    c2 = Complex(Rational(1), Rational(0))  # On real axis

    print(f"C1: {c1} (phase: {math.degrees(c1.phase):.1f}°)")
    print(f"C2: {c2} (phase: {math.degrees(c2.phase):.1f}°)")
    result = c1 * c2
    print(f"C1 × C2: {result} (phase: {math.degrees(result.phase):.1f}°)")
    print("  -> Complex multiplication rotates vectors")


def experiment_dimension_from_constraints():
    """
    Experiment: How constraints reduce effective dimension.

    From the document: "If you lock the length, there is only 1 degree
    of freedom... the whole line that moves in unison acts a lot like
    a point that moves along the line."
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Dimension from Constraints")
    print("=" * 60)

    # Free segment: 2 DOF
    print("\nFree segment (both endpoints free):")
    print("  DOF = 2 (start position, end position)")
    print("  Each end can move independently")

    # Fixed length: 1 DOF
    print("\nFixed-length segment:")
    print("  DOF = 1 (position only)")
    print("  Acts like a POINT moving along a line")
    print("  -> Constraint reduces dimension!")

    # Fixed start, free end: 1 DOF
    print("\nFixed-start segment:")
    print("  DOF = 1 (length only)")
    print("  This IS our number line! (unit at origin)")

    # Both fixed: 0 DOF
    print("\nFully constrained segment:")
    print("  DOF = 0")
    print("  This is a CONSTANT, not a variable")

    # Apply to complex numbers
    print("\n--- Complex number constraints ---")
    print("\nFree complex number:")
    print("  DOF = 4 (real_num, real_denom, imag_num, imag_denom)")

    print("\nComplex with fixed magnitude (on circle):")
    print("  DOF = 1 (angle only)")
    print("  -> This is why rotations are 1D in complex plane")

    print("\nComplex with fixed angle (on ray):")
    print("  DOF = 1 (magnitude only)")
    print("  -> This is scaling along a direction")


def experiment_type_escalation():
    """
    Experiment: How types change through operations.

    From the document: "Ops are always one or the other (LxW or m/s),
    never both (m*L/s)"
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Type Escalation and Reduction")
    print("=" * 60)

    # Define some typed ratios
    @dataclass
    class TypedRatio:
        value: Rational
        unit: str

        def __mul__(self, other: 'TypedRatio') -> 'TypedRatio':
            new_val = self.value * other.value
            new_unit = f"({self.unit}×{other.unit})"
            return TypedRatio(new_val, new_unit)

        def __truediv__(self, other: 'TypedRatio') -> 'TypedRatio':
            new_val = Rational(
                self.value.numerator * other.value.denominator,
                self.value.denominator * other.value.numerator
            )
            new_unit = f"({self.unit}/{other.unit})"
            return TypedRatio(new_val, new_unit)

        def __repr__(self):
            return f"{self.value.value:.2f} {self.unit}"

    # Distance and time -> speed
    distance = TypedRatio(Rational(100), "meters")
    time = TypedRatio(Rational(10), "seconds")
    speed = distance / time

    print(f"\nDistance: {distance}")
    print(f"Time: {time}")
    print(f"Speed: {speed}")

    # Speed and time -> acceleration
    speed2 = TypedRatio(Rational(20), "(meters/seconds)")
    acceleration = speed2 / time

    print(f"\nSpeed change: {speed2}")
    print(f"Over time: {time}")
    print(f"Acceleration: {acceleration}")

    # Area
    length = TypedRatio(Rational(5), "m")
    width = TypedRatio(Rational(3), "m")
    area = length * width

    print(f"\nLength: {length}")
    print(f"Width: {width}")
    print(f"Area: {area}")

    print("\nInsight: Types track what operations created them")
    print("        Division reduces type (m/s from m and s)")
    print("        Multiplication escalates type (m² from m and m)")


def experiment_number_system_hierarchy():
    """
    Experiment: The hierarchy of number systems.

    From document notes: "2 pts -> line, 2 lines -> rational,
    2 rationals -> complex (segment), 2 segments -> area"
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Number System Hierarchy")
    print("=" * 60)

    hierarchy = [
        ("1 point", 1, "existence", "•"),
        ("2 points", 2, "segment/natural", "•---•"),
        ("4 points", 4, "ratio/rational", "(•-•)/(•-•)"),
        ("8 points", 8, "complex", "real + imag×i"),
        ("16 points", 16, "quaternion", "w + xi + yj + zk"),
        ("32 points", 32, "octonion", "8 components"),
    ]

    print("\nNumber System Progression:")
    print("-" * 50)

    for name, points, system, notation in hierarchy:
        bits = int(math.log2(points)) if points > 0 else 0
        print(f"\n{name}:")
        print(f"  Points: {points} (2^{bits})")
        print(f"  System: {system}")
        print(f"  Notation: {notation}")

    print("\nPattern: Each level doubles the point count")
    print("         Each level adds new algebraic properties")
    print("         Each level can represent previous levels")


def main():
    """Run all number system experiments."""
    print("\n" + "=" * 70)
    print("NUMBER SYSTEMS AS COMPLEXITY SPACES")
    print("Completing the '2 Points' section and beyond")
    print("=" * 70)

    experiment_building_from_one_point()
    experiment_operations_emerge_from_structure()
    experiment_dimension_from_constraints()
    experiment_type_escalation()
    experiment_number_system_hierarchy()

    print("\n" + "=" * 70)
    print("SUMMARY: FROM 1 POINT TO NUMBER SYSTEMS")
    print("=" * 70)
    print("""
1. One Point (2^0 = 1):
   - Valid but uncharacterized
   - No measurement possible
   - The primitive, not information

2. Two Points (2^1 = 2):
   - Creates: length, direction, ordering
   - First measurable structure
   - DOF = 2 (each endpoint can move)
   - THIS IS WHERE MATH BEGINS

3. Four Points (2^2 = 4) - Rationals:
   - Creates: calibrated measurement
   - Numerator/denominator structure
   - Enables: fractions, precision, division

4. Eight Points (2^3 = 8) - Complex:
   - Creates: 2D algebraic space
   - Real + imaginary components
   - Enables: rotations, waves, oscillations

5. Sixteen Points (2^4 = 16) - Quaternions:
   - Creates: 3D rotations
   - Four components (w, x, y, z)
   - Enables: orientation in 3D

6. Key Insights:
   - Operations EMERGE from point configuration
   - Constraints REDUCE effective dimension
   - Types TRACK operational history
   - Each level CONTAINS all previous levels
""")


if __name__ == "__main__":
    main()
