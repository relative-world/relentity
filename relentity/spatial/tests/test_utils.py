import pytest
import numpy as np
from relentity.spatial.utils import do_edges_intersect, is_simple_polygon, point_in_polygon


@pytest.mark.parametrize(
    "p1, p2, p3, p4, expected",
    [
        (np.array([0, 0]), np.array([1, 1]), np.array([0, 1]), np.array([1, 0]), True),  # Intersecting
        (np.array([0, 0]), np.array([1, 1]), np.array([1, 0]), np.array([2, 1]), False),  # Non-intersecting
        (np.array([0, 0]), np.array([2, 2]), np.array([1, 1]), np.array([3, 3]), True),  # Collinear and overlapping
        (
            np.array([0, 0]),
            np.array([1, 1]),
            np.array([2, 2]),
            np.array([3, 3]),
            False,
        ),  # Collinear but not overlapping
    ],
)
def test_do_lines_intersect(p1, p2, p3, p4, expected):
    assert do_edges_intersect(p1, p2, p3, p4) == expected


@pytest.mark.parametrize(
    "polygon, expected",
    [
        ([(0, 0), (1, 1), (1, 0), (0, 1)], False),  # Self-intersecting
        ([(0, 0), (1, 0), (1, 1), (0, 1)], True),  # Simple square
        ([(0, 0), (2, 0), (1, 1), (2, 2), (0, 2)], True),  # Complex non-intersecting
        ([(0, 0), (2, 0), (2, 2), (0, 2)], True),  # Simple rectangle
    ],
)
def test_is_simple_polygon(polygon, expected):
    assert is_simple_polygon(polygon) == expected


@pytest.mark.parametrize(
    "x, y, polygon, expected",
    [
        (0.5, 0.5, [(0, 0), (1, 0), (1, 1), (0, 1)], True),  # Inside square
        (1.5, 1.5, [(0, 0), (1, 0), (1, 1), (0, 1)], False),  # Outside square
        (1, 1, [(0, 0), (2, 0), (2, 2), (0, 2)], True),  # On the edge of rectangle
        (3, 3, [(0, 0), (2, 0), (2, 2), (0, 2)], False),  # Outside rectangle
    ],
)
def test_point_in_polygon(x, y, polygon, expected):
    assert point_in_polygon(x, y, polygon) == expected
