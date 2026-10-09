"""The distance tool's angle row shows the measured angle and its supplement.

`get_distance` answers the panel, which prints a string as it is, so the angle
goes there as "angle (180 - angle)" - vscode-ocp-cad-viewer issue 236.
`calc_angle` stays numeric for whoever computes with it.
"""

from math import sqrt

import build123d as bd
import pytest
from ocp_viewer_core import measure
from ocp_viewer_core.measure import calc_angle, get_distance


def _angle_row(shape1, shape2):
    return get_distance(shape1.wrapped, shape2.wrapped, center=False)["result"][2]["angle"]


def test_perpendicular_lines_show_90_twice():
    assert _angle_row(bd.Line((0, 0, 0), (10, 0, 0)), bd.Line((0, 0, 0), (0, 10, 0))) == "90.000 (90.000)"


def test_60_degrees_show_their_supplement():
    line1 = bd.Line((0, 0, 0), (10, 0, 0))
    line2 = bd.Line((0, 0, 0), (5, 5 * sqrt(3), 0))
    assert _angle_row(line1, line2) == "60.000 (120.000)"


def test_calc_angle_stays_a_number():
    line1 = bd.Line((0, 0, 0), (10, 0, 0))
    line2 = bd.Line((0, 0, 0), (5, 5 * sqrt(3), 0))
    assert calc_angle(line1.wrapped, line2.wrapped)["angle"] == pytest.approx(60)


def test_a_vertex_has_no_angle_row():
    result = get_distance(bd.Vertex(5, 5, 0).wrapped, bd.Line((0, 0, 0), (10, 0, 0)).wrapped, center=False)["result"]
    assert len(result) == 2


def test_a_rounding_error_past_180_shows_no_negative_zero(monkeypatch):
    real = measure.calc_angle

    def past_180(shape1, shape2):
        response = real(shape1, shape2)
        response["angle"] = 180.0000000001
        return response

    monkeypatch.setattr(measure, "calc_angle", past_180)
    row = _angle_row(bd.Line((0, 0, 0), (10, 0, 0)), bd.Line((0, 0, 0), (0, 10, 0)))
    assert row == "180.000 (0.000)"
