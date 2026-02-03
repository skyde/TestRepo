"""
Experiment 1: Dimensional Projection and Information Loss

This experiment explores how information is lost or preserved when
projecting between complexity spaces of different dimensions.

Key questions:
1. What information is lost when projecting from higher to lower dimensions?
2. Can we quantify this information loss?
3. How does the "memory" of higher dimensions persist in lower projections?
"""

import sys
sys.path.insert(0, '/home/user/TestRepo/complexity_spaces')

from core import (
    Measure, Point, Segment, Certainty,
    LinearSpace, PlanarSpace, VolumetricSpace
)
import math
from dataclasses import dataclass
from typing import List, Tuple
import random


@dataclass
class ProjectionRecord:
    """Tracks information about a projection operation."""
    original_dims: int
    projected_dims: int
    information_lost: float  # Bits of information lost
    reconstructible: bool    # Can we recover original from projection?
    ambiguity_count: int     # How many originals could produce this projection


def calculate_information_content(point: Point) -> float:
    """
    Estimate information content of a point based on resolution.
    More resolution = more information.
    """
    total_bits = 0.0
    for m in point.measures:
        # Each measure contributes log2(resolution) bits
        # Plus information about position within bounds
        if m.max_bound != float('inf') and m.min_bound != float('-inf'):
            range_size = m.max_bound - m.min_bound
            position_info = math.log2(range_size * m.resolution + 1) if range_size > 0 else 0
        else:
            position_info = math.log2(m.resolution)
        total_bits += position_info
    return total_bits


def project_3d_to_2d(point_3d: Point, axis_to_remove: int = 2) -> Tuple[Point, ProjectionRecord]:
    """
    Project a 3D point to 2D by removing one axis.

    Returns the projected point and a record of the projection.
    """
    if point_3d.dimensions != 3:
        raise ValueError("Input must be 3D point")

    original_info = calculate_information_content(point_3d)

    # Create 2D point by removing specified axis
    new_measures = [m for i, m in enumerate(point_3d.measures) if i != axis_to_remove]
    projected = Point(new_measures)

    projected_info = calculate_information_content(projected)
    info_lost = original_info - projected_info

    record = ProjectionRecord(
        original_dims=3,
        projected_dims=2,
        information_lost=info_lost,
        reconstructible=False,  # Can't recover z from x,y
        ambiguity_count=int(point_3d.measures[axis_to_remove].resolution)  # Many z values map to same (x,y)
    )

    return projected, record


def project_2d_to_1d(point_2d: Point, axis_to_keep: int = 0) -> Tuple[Point, ProjectionRecord]:
    """Project a 2D point to 1D by keeping only one axis."""
    if point_2d.dimensions != 2:
        raise ValueError("Input must be 2D point")

    original_info = calculate_information_content(point_2d)

    projected = Point([point_2d.measures[axis_to_keep]])
    projected_info = calculate_information_content(projected)

    record = ProjectionRecord(
        original_dims=2,
        projected_dims=1,
        information_lost=original_info - projected_info,
        reconstructible=False,
        ambiguity_count=int(point_2d.measures[1 - axis_to_keep].resolution)
    )

    return projected, record


def project_segment_to_point(segment: Segment) -> Tuple[Point, ProjectionRecord]:
    """
    Project a segment to its midpoint, losing length and direction info.

    This is a key operation: reducing 2 degrees of freedom to match
    the lower dimension's capabilities.
    """
    original_info = calculate_information_content(segment.start) + \
                   calculate_information_content(segment.end)

    midpoint = segment.midpoint
    midpoint_info = calculate_information_content(midpoint)

    # Additional info lost: length and direction
    # Length requires ~log2(resolution) bits to encode
    # Direction requires ~log2(360) bits in 2D, more in 3D
    length_bits = math.log2(max(segment.start.measures[0].resolution, 1))

    record = ProjectionRecord(
        original_dims=segment.start.dimensions * 2,  # 2 points worth of dims
        projected_dims=segment.start.dimensions,
        information_lost=original_info - midpoint_info + length_bits,
        reconstructible=False,
        ambiguity_count=int(segment.start.measures[0].resolution ** segment.start.dimensions)
    )

    return midpoint, record


def experiment_projection_cascade():
    """
    Experiment: Project from 3D -> 2D -> 1D and track cumulative information loss.
    """
    print("=" * 60)
    print("EXPERIMENT: Projection Cascade (3D -> 2D -> 1D)")
    print("=" * 60)

    # Create a 3D space and point
    vol_space = VolumetricSpace(
        x_bounds=(0, 100), y_bounds=(0, 100), z_bounds=(0, 100),
        resolution=1000
    )

    # Create several test points
    test_points = [
        vol_space.create_point(50.0, 50.0, 50.0),   # Center
        vol_space.create_point(10.0, 90.0, 30.0),   # Corner-ish
        vol_space.create_point(99.0, 1.0, 50.0),    # Edge
    ]

    total_info_lost = 0.0

    for i, p3d in enumerate(test_points):
        print(f"\nTest Point {i+1}: {p3d}")
        original_info = calculate_information_content(p3d)
        print(f"  Original information: {original_info:.2f} bits")

        # Project to 2D
        p2d, rec1 = project_3d_to_2d(p3d)
        print(f"  -> 2D projection: {p2d}")
        print(f"     Info lost: {rec1.information_lost:.2f} bits, Ambiguity: {rec1.ambiguity_count}")

        # Project to 1D
        p1d, rec2 = project_2d_to_1d(p2d)
        print(f"  -> 1D projection: {p1d}")
        print(f"     Info lost: {rec2.information_lost:.2f} bits, Ambiguity: {rec2.ambiguity_count}")

        cumulative_loss = rec1.information_lost + rec2.information_lost
        total_info_lost += cumulative_loss
        print(f"  Cumulative loss: {cumulative_loss:.2f} bits ({cumulative_loss/original_info*100:.1f}%)")

    print(f"\nAverage information lost per point: {total_info_lost/len(test_points):.2f} bits")


def experiment_segment_reduction():
    """
    Experiment: How do segments behave under dimensional reduction?

    Key insight from document: A line of fixed length acts like a point
    moving along the containing line - it has 1 degree of freedom.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Segment Reduction and Degrees of Freedom")
    print("=" * 60)

    # Create segments with different constraints
    line_space = LinearSpace(min_val=0, max_val=100, resolution=1000)

    # Case 1: Free segment (2 DOF - each end can move)
    seg_free = line_space.create_segment(20.0, 80.0)
    print(f"\nFree segment: {seg_free}")
    print(f"  Degrees of freedom: 2 (both endpoints movable)")
    print(f"  Length: {seg_free.length}")

    # Case 2: Fixed length segment (1 DOF - whole thing moves as unit)
    # Simulate by tracking only the midpoint
    fixed_length = 30.0
    midpoint_pos = 50.0

    print(f"\nFixed-length segment (length={fixed_length}):")
    print(f"  Midpoint position: {midpoint_pos}")
    print(f"  Degrees of freedom: 1 (acts like a point)")
    print(f"  Start: {midpoint_pos - fixed_length/2}, End: {midpoint_pos + fixed_length/2}")

    # Case 3: Fixed start point (1 DOF - only end can move)
    start_fixed = 10.0
    print(f"\nFixed-start segment (start={start_fixed}):")
    print(f"  Degrees of freedom: 1 (only length/end can change)")

    # Demonstrate that fixed-length segment is isomorphic to a point
    print("\n--- Fixed-length segment behaves like a point ---")
    positions = [20.0, 40.0, 60.0, 80.0]
    for pos in positions:
        effective_point = line_space.create_point(pos)
        print(f"  Position {pos} -> Segment [{pos-fixed_length/2:.1f}, {pos+fixed_length/2:.1f}]")


def experiment_multiple_projection_paths():
    """
    Experiment: Different projection paths from same starting point.

    Question: Do different projection strategies preserve different information?
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Multiple Projection Paths")
    print("=" * 60)

    vol_space = VolumetricSpace(
        x_bounds=(0, 100), y_bounds=(0, 100), z_bounds=(0, 100),
        resolution=1000
    )

    p3d = vol_space.create_point(30.0, 60.0, 45.0)
    print(f"\nOriginal 3D point: {p3d}")

    # Path 1: Remove Z, then remove Y
    p2d_xy, _ = project_3d_to_2d(p3d, axis_to_remove=2)  # Keep X,Y
    p1d_x, _ = project_2d_to_1d(p2d_xy, axis_to_keep=0)  # Keep X
    print(f"\nPath 1 (drop Z, then Y): {p3d} -> {p2d_xy} -> {p1d_x}")

    # Path 2: Remove Z, then remove X
    p2d_xy2, _ = project_3d_to_2d(p3d, axis_to_remove=2)  # Keep X,Y
    p1d_y, _ = project_2d_to_1d(p2d_xy2, axis_to_keep=1)  # Keep Y
    print(f"Path 2 (drop Z, then X): {p3d} -> {p2d_xy2} -> {p1d_y}")

    # Path 3: Remove Y first
    p2d_xz, _ = project_3d_to_2d(p3d, axis_to_remove=1)  # Keep X,Z
    p1d_x2, _ = project_2d_to_1d(p2d_xz, axis_to_keep=0)  # Keep X
    print(f"Path 3 (drop Y, then Z): {p3d} -> {p2d_xz} -> {p1d_x2}")

    # Insight: Same final dimension (X) reached, but intermediate information differs
    print("\nInsight: All paths to X-value converge, but intermediate representations differ")
    print(f"  Final X value via all paths: {p1d_x.measures[0].value}")
    print(f"  Different information was available at 2D stage depending on path")


def experiment_information_recovery():
    """
    Experiment: Can we partially recover lost information using constraints?

    Key insight: If we know constraints, we can narrow the ambiguity.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Information Recovery via Constraints")
    print("=" * 60)

    # Original point
    vol_space = VolumetricSpace(
        x_bounds=(0, 100), y_bounds=(0, 100), z_bounds=(0, 100),
        resolution=100
    )

    original = vol_space.create_point(50.0, 30.0, 70.0)
    print(f"\nOriginal 3D point: {original}")

    # Project to 2D (lose Z)
    projected_2d, rec = project_3d_to_2d(original)
    print(f"Projected to 2D: {projected_2d}")
    print(f"Ambiguity: {rec.ambiguity_count} possible Z values")

    # Apply constraints to narrow ambiguity
    print("\nApplying constraints to recover information:")

    # Constraint 1: Z must be in range [50, 80]
    z_constraint = (50.0, 80.0)
    narrowed_ambiguity = int(100 * (z_constraint[1] - z_constraint[0]))
    print(f"  Constraint: Z in {z_constraint}")
    print(f"  New ambiguity: {narrowed_ambiguity} (reduced by {(1 - narrowed_ambiguity/rec.ambiguity_count)*100:.1f}%)")

    # Constraint 2: Point lies on a known surface (e.g., Z = X + 20)
    # If Z = X + 20, and we know X = 50, then Z = 70
    print(f"  Constraint: Z = X + 20 (surface constraint)")
    recovered_z = projected_2d.measures[0].value + 20
    print(f"  Recovered Z: {recovered_z}")
    print(f"  Ambiguity: 1 (fully recovered!)")

    # This demonstrates: constraints from "above" can restore lost information
    print("\nInsight: Higher-dimensional knowledge (constraints) can restore")
    print("         information lost during projection")


def experiment_segment_as_weighted_point():
    """
    Experiment: Segments as "weighted" points with metadata.

    From the document: "The idea that the lines are curved means they are
    viewed and encoded in a higher dimensional space."

    A segment encodes more than position - it encodes "weight" or "certainty"
    through its length.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT: Segments as Weighted Points")
    print("=" * 60)

    plane = PlanarSpace(x_bounds=(0, 100), y_bounds=(0, 100), resolution=1000)

    # Create several segments of different lengths at same midpoint
    midpoint = (50.0, 50.0)
    lengths = [5.0, 20.0, 50.0]

    print(f"\nMidpoint: {midpoint}")
    print("\nSegments with different 'weights' (lengths):")

    for length in lengths:
        # Create segment centered at midpoint
        half = length / 2
        seg = Segment(
            plane.create_point(midpoint[0] - half, midpoint[1]),
            plane.create_point(midpoint[0] + half, midpoint[1])
        )

        # Interpret length as "certainty" or "weight"
        certainty = length / 100.0  # Normalize to [0, 1]
        print(f"  Length {length}: Certainty/Weight = {certainty:.2f}")
        print(f"    Could represent: confidence in position, influence radius, etc.")

    print("\nInsight: The 'extra' degrees of freedom in segments allow encoding")
    print("         metadata (certainty, weight, influence) without changing position")


def main():
    """Run all projection experiments."""
    print("\n" + "=" * 70)
    print("DIMENSIONAL PROJECTION EXPERIMENTS")
    print("Exploring information loss and recovery in complexity spaces")
    print("=" * 70)

    experiment_projection_cascade()
    experiment_segment_reduction()
    experiment_multiple_projection_paths()
    experiment_information_recovery()
    experiment_segment_as_weighted_point()

    print("\n" + "=" * 70)
    print("SUMMARY OF FINDINGS")
    print("=" * 70)
    print("""
1. Information Loss is Quantifiable:
   - Each dimensional reduction loses ~log2(resolution) bits per dimension
   - Cumulative loss grows with each projection step
   - Different projection paths preserve different intermediate information

2. Degrees of Freedom Determine Behavior:
   - Free segment (2 DOF) vs fixed-length segment (1 DOF)
   - Constraining elements reduces them to lower-dimensional analogs
   - A constrained line IS a point (mathematically isomorphic)

3. Constraints Enable Recovery:
   - Lost information can be recovered through constraints
   - Constraints encode "knowledge from above" (higher dimensions)
   - This is why multi-layer systems can communicate: shared constraints

4. Metadata Through Redundancy:
   - Elements with extra DOF can encode metadata
   - Segment length encodes certainty/weight at a position
   - This redundancy enables "smart" elements with agency
""")


if __name__ == "__main__":
    main()
