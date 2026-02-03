"""
Experiment 3: Error as Learning Signal at Multiple Levels

From the document:
"The opportunity here is that error is quantifiable and correctable...
If our measures can have error without needing to search the metadata
of allowed values, this means learning can happen in every perspective,
at every layer of complexity."

This experiment explores:
1. Error in value vs error in frame
2. How error propagates across layers
3. Error as a gradient for learning
"""

import sys
sys.path.insert(0, '/home/user/TestRepo/complexity_spaces')

from core import Measure, Point, Segment, Certainty
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto


class ErrorType(Enum):
    """Types of error in a complexity space."""
    VALUE_ERROR = auto()      # Value is wrong but type is right
    RESOLUTION_ERROR = auto() # Measured at wrong precision
    BOUNDS_ERROR = auto()     # Value outside valid range
    TYPE_ERROR = auto()       # Wrong category entirely
    FRAME_ERROR = auto()      # Using wrong reference frame


@dataclass
class ErrorReport:
    """Detailed error analysis."""
    error_type: ErrorType
    magnitude: float
    correction_direction: Optional[List[float]]
    correctable_at_layer: int  # Which layer can fix this
    description: str


@dataclass
class BoundedMeasure:
    """
    A measure with explicit bounds that define valid range.

    From the document: "When we create a complexity space, not only do
    we need to specify the parameters and their transforms, we also
    need to specify the resolution and bounds."
    """
    value: float
    min_bound: float
    max_bound: float
    resolution: int = 1000
    unit_name: str = "unit"

    def __post_init__(self):
        # Quantize to resolution
        self.value = round(self.value * self.resolution) / self.resolution

    @property
    def is_valid(self) -> bool:
        """Check if value is within bounds."""
        return self.min_bound <= self.value <= self.max_bound

    @property
    def validity_score(self) -> float:
        """
        Returns 1.0 if valid, 0-1 based on how far out of bounds.
        """
        if self.is_valid:
            return 1.0

        range_size = self.max_bound - self.min_bound
        if range_size <= 0:
            return 0.0

        if self.value < self.min_bound:
            error = self.min_bound - self.value
        else:
            error = self.value - self.max_bound

        return max(0.0, 1.0 - error / range_size)

    def error_direction(self) -> float:
        """Direction to move to reduce error (-1, 0, or 1)."""
        if self.is_valid:
            return 0.0
        return 1.0 if self.value < self.min_bound else -1.0

    def error_magnitude(self) -> float:
        """How far outside bounds."""
        if self.is_valid:
            return 0.0
        if self.value < self.min_bound:
            return self.min_bound - self.value
        return self.value - self.max_bound

    def correct(self, amount: float) -> 'BoundedMeasure':
        """Apply correction and return new measure."""
        new_value = self.value + amount
        return BoundedMeasure(
            value=new_value,
            min_bound=self.min_bound,
            max_bound=self.max_bound,
            resolution=self.resolution,
            unit_name=self.unit_name
        )

    def analyze_error(self) -> ErrorReport:
        """Generate detailed error report."""
        if self.is_valid:
            return ErrorReport(
                error_type=ErrorType.VALUE_ERROR,
                magnitude=0.0,
                correction_direction=None,
                correctable_at_layer=0,
                description="No error - value within bounds"
            )

        return ErrorReport(
            error_type=ErrorType.BOUNDS_ERROR,
            magnitude=self.error_magnitude(),
            correction_direction=[self.error_direction()],
            correctable_at_layer=0,  # Can fix at this layer
            description=f"Value {self.value} outside bounds [{self.min_bound}, {self.max_bound}]"
        )


@dataclass
class CategoryBounds:
    """
    Defines bounds for a category (like "dog weight" from the document).

    From the document: "A dog can be any weight, but outside certain ranges,
    it is no longer a dog."
    """
    category_name: str
    measures: Dict[str, Tuple[float, float]]  # name -> (min, max)

    def contains(self, instance: Dict[str, float]) -> bool:
        """Check if instance fits category."""
        for name, (min_val, max_val) in self.measures.items():
            if name in instance:
                if not (min_val <= instance[name] <= max_val):
                    return False
        return True

    def category_error(self, instance: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """
        Compute how far instance is from being in category.
        Returns (total_error, corrections_needed).
        """
        total_error = 0.0
        corrections = {}

        for name, (min_val, max_val) in self.measures.items():
            if name in instance:
                val = instance[name]
                if val < min_val:
                    error = min_val - val
                    corrections[name] = error
                    total_error += error
                elif val > max_val:
                    error = val - max_val
                    corrections[name] = -error
                    total_error += error

        return total_error, corrections


@dataclass
class LayeredValue:
    """
    A value that exists in multiple layers simultaneously.

    Each layer has its own bounds and can contribute error signals.
    """
    base_value: float
    layers: List[BoundedMeasure]  # Same value, different bounds per layer

    def total_error(self) -> float:
        """Sum of errors across all layers."""
        return sum(layer.error_magnitude() for layer in self.layers)

    def layer_errors(self) -> List[ErrorReport]:
        """Error reports from each layer."""
        return [layer.analyze_error() for layer in self.layers]

    def negotiate_correction(self) -> float:
        """
        Compute correction that best satisfies all layers.

        This is where "intelligence distributed through spaces" manifests:
        each layer contributes its error gradient, and the value moves
        toward the configuration that minimizes total error.
        """
        # Weighted average of correction directions
        total_weight = 0.0
        weighted_correction = 0.0

        for layer in self.layers:
            error = layer.error_magnitude()
            direction = layer.error_direction()

            if error > 0:
                # Weight by error magnitude (larger errors get more say)
                weighted_correction += direction * error
                total_weight += error

        if total_weight > 0:
            return weighted_correction / total_weight * 0.5  # Dampened
        return 0.0


def experiment_value_vs_frame_error():
    """
    Experiment: Distinguish between value error and frame error.

    From the document: "If I was to guess the weight of your mother...
    the errors fall into two categories."
    """
    print("=" * 60)
    print("EXPERIMENT: Value Error vs Frame Error")
    print("=" * 60)

    # Define "adult human weight" category
    human_weight = CategoryBounds(
        category_name="adult_human_weight",
        measures={
            "weight_kg": (30, 300),  # Reasonable bounds for adult humans
        }
    )

    test_cases = [
        {"weight_kg": 70},    # Normal - no error
        {"weight_kg": 150},   # Valid but high
        {"weight_kg": 300},   # Edge of valid
        {"weight_kg": 500},   # Category error - too high
        {"weight_kg": 2},     # Category error - too low (baby?)
        {"weight_kg": 9000},  # Extreme category error (elephant?)
    ]

    print(f"\nCategory: {human_weight.category_name}")
    print(f"Valid range: {human_weight.measures['weight_kg']}")

    for case in test_cases:
        weight = case["weight_kg"]
        in_category = human_weight.contains(case)
        error, corrections = human_weight.category_error(case)

        status = "VALID" if in_category else "CATEGORY ERROR"
        print(f"\n  Weight: {weight} kg -> {status}")
        if not in_category:
            print(f"    Error magnitude: {error:.1f}")
            print(f"    Correction needed: {corrections}")
            if error > 200:
                print(f"    Analysis: Likely wrong category entirely (not human?)")
            elif error > 50:
                print(f"    Analysis: Bounds need updating or measurement error")
            else:
                print(f"    Analysis: Minor bounds violation")


def experiment_resolution_error():
    """
    Experiment: Error from measuring at wrong resolution.

    From the document: "½ is lower resolution than 2/4, which is lower
    resolution than 1000/2000."
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Resolution Error")
    print("=" * 60)

    # Same value at different resolutions
    value = 0.333333

    resolutions = [10, 100, 1000, 10000]
    print(f"\nOriginal value: {value}")
    print(f"Representing at different resolutions:")

    prev_val = None
    for res in resolutions:
        quantized = round(value * res) / res
        error = abs(value - quantized)

        if prev_val is not None:
            info_gain = math.log2(res / (res // 10))  # Bits gained
        else:
            info_gain = 0

        print(f"\n  Resolution 1/{res}:")
        print(f"    Quantized value: {quantized}")
        print(f"    Quantization error: {error:.6f}")
        print(f"    Information bits: ~{math.log2(res):.1f}")

        prev_val = quantized

    print("\nInsight: Resolution determines precision, but also information cost")
    print("        Lower resolution = less information to store/transmit")


def experiment_multi_layer_error_propagation():
    """
    Experiment: How error propagates through multiple layers.

    Key insight: A value can be valid in one layer but invalid in another.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Multi-Layer Error Propagation")
    print("=" * 60)

    # Create a value that exists in multiple conceptual layers
    # Layer 0: Raw measurement (any value)
    # Layer 1: Physical constraint (must be positive)
    # Layer 2: Domain constraint (speed < speed of light)
    # Layer 3: Practical constraint (car speed < 300 km/h)

    test_values = [50, 150, 350, -10, 500000]

    for val in test_values:
        print(f"\nValue: {val} km/h")

        layers = [
            BoundedMeasure(val, float('-inf'), float('inf'), unit_name="raw"),
            BoundedMeasure(val, 0, float('inf'), unit_name="physical"),
            BoundedMeasure(val, 0, 1080000000, unit_name="relativistic"),  # < c
            BoundedMeasure(val, 0, 300, unit_name="car_speed"),
        ]

        layered = LayeredValue(val, layers)

        for i, layer in enumerate(layers):
            report = layer.analyze_error()
            status = "OK" if report.magnitude == 0 else f"ERROR({report.magnitude:.0f})"
            print(f"  Layer {i} ({layer.unit_name}): {status}")

        # Compute negotiated correction
        correction = layered.negotiate_correction()
        if abs(correction) > 0.001:
            print(f"  Suggested correction: {correction:.1f}")
            print(f"  (Move value toward {val + correction:.1f})")


def experiment_error_gradient_learning():
    """
    Experiment: Using error as gradient for iterative learning.

    This is the key to "learning at every layer":
    - Each layer computes its error gradient
    - The system moves in the direction that reduces total error
    - Learning happens without explicit backpropagation
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Error Gradient Learning")
    print("=" * 60)

    # Scenario: A value trying to satisfy multiple conflicting constraints
    # Layer 1: Wants value > 50
    # Layer 2: Wants value < 40
    # Layer 3: Wants value near 45

    class ConflictingLayers:
        def __init__(self, value: float):
            self.value = value
            self.history = [value]

        def layer_errors(self) -> List[Tuple[str, float, float]]:
            """Returns (name, error, gradient) for each layer."""
            errors = []

            # Layer 1: Error if < 50
            if self.value < 50:
                errors.append(("min_50", 50 - self.value, 1.0))
            else:
                errors.append(("min_50", 0, 0))

            # Layer 2: Error if > 40
            if self.value > 40:
                errors.append(("max_40", self.value - 40, -1.0))
            else:
                errors.append(("max_40", 0, 0))

            # Layer 3: Error based on distance from 45
            dist = abs(self.value - 45)
            gradient = -1.0 if self.value > 45 else 1.0
            errors.append(("target_45", dist, gradient))

            return errors

        def total_error(self) -> float:
            return sum(e[1] for e in self.layer_errors())

        def compute_gradient(self) -> float:
            """Weighted average of gradients."""
            errors = self.layer_errors()
            total_weight = sum(e[1] + 0.1 for e in errors)  # +0.1 to avoid div0
            weighted_grad = sum(e[1] * e[2] for e in errors)
            return weighted_grad / total_weight if total_weight > 0 else 0

        def step(self, learning_rate: float = 0.1):
            """Take one learning step."""
            grad = self.compute_gradient()
            self.value += learning_rate * grad
            self.history.append(self.value)

    # Run learning
    initial_values = [0, 100, 45, 60]

    for init_val in initial_values:
        learner = ConflictingLayers(init_val)

        print(f"\nStarting value: {init_val}")
        print(f"  Initial errors: {[(e[0], f'{e[1]:.1f}') for e in learner.layer_errors()]}")

        # Run for several steps
        for step in range(20):
            learner.step(learning_rate=0.3)

        final_errors = learner.layer_errors()
        print(f"  Final value: {learner.value:.2f}")
        print(f"  Final errors: {[(e[0], f'{e[1]:.1f}') for e in final_errors]}")
        print(f"  Total error: {learner.total_error():.2f}")

    print("\nInsight: Value converges to ~45 - the best compromise")
    print("        No single layer is fully satisfied, but total error is minimized")


def experiment_segment_error_geometry():
    """
    Experiment: Error in geometric configurations.

    From the document: "Imagine a segment on a numberline. Many possible
    points will not be in this segment, but they will know what direction
    they need to move."
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Geometric Error as Direction")
    print("=" * 60)

    # Define a segment
    segment_start = 30
    segment_end = 70

    # Test various points
    test_points = [10, 30, 50, 70, 90, 45]

    print(f"\nSegment: [{segment_start}, {segment_end}]")
    print(f"\nTest points and their 'knowledge' about the segment:")

    for point in test_points:
        in_segment = segment_start <= point <= segment_end

        if in_segment:
            print(f"\n  Point {point}: IN segment")
            # Point knows it's contained - might want to stay centered
            center = (segment_start + segment_end) / 2
            direction = "toward center" if point != center else "stay"
            print(f"    Desire: {direction} ({center})")
        else:
            print(f"\n  Point {point}: OUTSIDE segment")
            if point < segment_start:
                direction = "right (toward segment)"
                distance = segment_start - point
            else:
                direction = "left (toward segment)"
                distance = point - segment_end
            print(f"    Direction to enter: {direction}")
            print(f"    Distance to segment: {distance}")

    # Two segments that might not intersect
    print("\n--- Two segments in 2D ---")
    seg1 = {"x": (20, 80), "y": (40, 40)}  # Horizontal line at y=40
    seg2 = {"x": (50, 50), "y": (60, 100)} # Vertical line at x=50

    # Do they intersect?
    x_overlap = max(seg1["x"][0], seg2["x"][0]) <= min(seg1["x"][1], seg2["x"][1])
    y_overlap = max(seg1["y"][0], seg2["y"][0]) <= min(seg1["y"][1], seg2["y"][1])

    print(f"\nSegment 1: x={seg1['x']}, y={seg1['y']}")
    print(f"Segment 2: x={seg2['x']}, y={seg2['y']}")
    print(f"X overlap: {x_overlap}")
    print(f"Y overlap: {y_overlap}")
    print(f"Intersect: {x_overlap and y_overlap}")

    if not (x_overlap and y_overlap):
        print("\nSegments don't intersect - but they can 'negotiate':")
        print("  Seg1 could move up (increase y)")
        print("  Seg2 could extend down (decrease y)")
        print("  Or both move toward each other")


def main():
    """Run all error experiments."""
    print("\n" + "=" * 70)
    print("ERROR AS LEARNING SIGNAL EXPERIMENTS")
    print("Exploring quantifiable, correctable error at every layer")
    print("=" * 70)

    experiment_value_vs_frame_error()
    experiment_resolution_error()
    experiment_multi_layer_error_propagation()
    experiment_error_gradient_learning()
    experiment_segment_error_geometry()

    print("\n" + "=" * 70)
    print("SUMMARY OF FINDINGS")
    print("=" * 70)
    print("""
1. Two Types of Error:
   - Value error: measurement within correct frame but wrong value
   - Frame error: wrong category, resolution, or reference entirely
   - Frame errors require updating the space, not just the value

2. Resolution as Information:
   - Higher resolution = more information = more storage cost
   - Quantization error is unavoidable but quantifiable
   - Choose resolution based on what precision matters

3. Multi-Layer Error:
   - A value can be valid in one layer, invalid in another
   - Each layer contributes error signals independently
   - Total system error is the sum across layers

4. Error as Gradient:
   - Error magnitude tells HOW MUCH to change
   - Error direction tells WHICH WAY to change
   - Learning = iteratively following error gradient

5. Geometric Error:
   - Points "know" which direction leads to segments
   - Segments "know" which direction leads to intersection
   - This directional knowledge IS the learning signal

6. Key Insight from Document:
   "If our measures can have error without needing to search
    the metadata of allowed values, this means learning can
    happen in every perspective, at every layer of complexity."
""")


if __name__ == "__main__":
    main()
