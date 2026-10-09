"""ColorMap.golden_ratio(hue_offset=...) shifts where the walk starts.

A fraction of the colormap, 0 to 1, applied to the first color and to every
later one; 0 keeps the former colors, and it is applied before `reverse`
(vscode-ocp-cad-viewer issue 222).
"""

import pytest
from ocp_viewer_core.colors import ColorMap, hsv_mapper, matplotlib_mapper

PHI_INV = 2 / (1 + 5**0.5)


def _walk(colormap, n=6):
    return [next(colormap) for _ in range(n)]


def _expected(mapper, ts, alpha=1.0, **params):
    return [(*mapper(t, **params), alpha) for t in ts]


def test_no_offset_keeps_the_former_colors():
    ts = [(PHI_INV * i) % 1 for i in range(6)]
    assert _walk(ColorMap.golden_ratio()) == _expected(hsv_mapper, ts)


def test_an_offset_shifts_the_first_color_and_every_later_one():
    ts = [(0.5 + PHI_INV * i) % 1 for i in range(6)]
    assert _walk(ColorMap.golden_ratio(hue_offset=0.5)) == _expected(hsv_mapper, ts)


def test_a_whole_turn_is_no_offset():
    # Equal up to rounding: (1 + x) % 1 is x in the last bits only.
    turned, plain = _walk(ColorMap.golden_ratio(hue_offset=1.0)), _walk(ColorMap.golden_ratio())
    for a, b in zip(turned, plain, strict=True):
        assert a == pytest.approx(b)


def test_the_offset_is_applied_before_reverse():
    ts = [1 - (0.25 + PHI_INV * i) % 1 for i in range(6)]
    colormap = ColorMap.golden_ratio(hue_offset=0.25, reverse=True)
    assert _walk(colormap) == _expected(hsv_mapper, ts)


def test_reset_starts_again_at_the_offset():
    colormap = ColorMap.golden_ratio(hue_offset=0.3)
    first = _walk(colormap)
    colormap.reset()
    assert _walk(colormap) == first


def test_a_matplotlib_colormap_is_shifted_along_its_length():
    pytest.importorskip("matplotlib")
    ts = [(0.4 + PHI_INV * i) % 1 for i in range(6)]
    # jet, because matplotlib_mapper takes linear segmented colormaps only.
    colormap = ColorMap.golden_ratio("mpl:jet", alpha=0.5, hue_offset=0.4)
    assert _walk(colormap) == _expected(matplotlib_mapper, ts, alpha=0.5, name="jet")
