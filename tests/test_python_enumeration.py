"""`python_enumeration` reaches ocp-tessellate's converter from every config level.

Repeated names are numbered from 0 like Python indices by default: the
built-in default is True and every host stores True (vscode-ocp-cad-viewer
issue 242). The names are the tree paths, and paths are an API - animation
tracks, saved states and selections address objects by them - so a stored
False, `set_defaults(python_enumeration=False)` or the show keyword brings the
former names back. It is ocp-tessellate's alone: the viewer receives the
names, never the flag.
"""

import pytest
from build123d import Box, Pos
from ocp_viewer_core.comms import Comms, Session
from ocp_viewer_core.config import DEFAULT_DEFAULTS, Config
from ocp_viewer_core.show import Viewer

OLD = ["/Group", "/Group/Solid", "/Group/Solid(2)", "/Group/Solid(3)"]
PYTHON = ["/Group", "/Group/Solid(0)", "/Group/Solid(1)", "/Group/Solid(2)"]


class StoredComms(Comms[None]):
    """A host with a stored config, a viewer that reports nothing, and a model sink."""

    def __init__(self, stored):
        super().__init__()
        self.stored = {"_splash": False, **stored}
        self.sent = []

    def workspace_config(self):
        return dict(self.stored)

    def status(self):
        return {}

    def send_data(self, data, port=None, timeit=False):
        self.sent.append(data)

    def send_backend(self, data, port=None, timeit=False):
        pass

    def send_config(self, config, timeit=False):
        pass


def _show(stored, **kwargs):
    viewer = Viewer(Config(Session(StoredComms(stored)), exclude_keys=()))
    boxes = [Pos(2 * i, 0, 0) * Box(1, 1, 1) for i in range(3)]
    viewer.show(*boxes, progress=None, **kwargs)
    _assert_not_sent(viewer)
    return viewer


def _assert_not_sent(viewer):
    """The flag is ocp-tessellate's; what it produced is in the names, and the
    viewer is never told the flag itself, in either spelling."""
    sent = viewer.config.session.comms.sent
    assert len(sent) > 0
    for data in sent:
        assert "python_enumeration" not in data["config"]
        assert "pythonEnumeration" not in data["config"]


def test_the_default_numbers_from_zero():
    assert DEFAULT_DEFAULTS["python_enumeration"] is True
    assert _show({}).last_paths == PYTHON


def test_a_stored_true_numbers_from_zero():
    assert _show({"python_enumeration": True}).last_paths == PYTHON


def test_a_stored_false_keeps_the_former_names():
    assert _show({"python_enumeration": False}).last_paths == OLD


def test_a_show_keyword_beats_the_stored_setting():
    assert _show({"python_enumeration": True}, python_enumeration=False).last_paths == OLD
    assert _show({"python_enumeration": False}, python_enumeration=True).last_paths == PYTHON


@pytest.mark.parametrize("value, expected", [(True, PYTHON), (False, OLD)])
def test_set_defaults_beats_the_stored_setting(value, expected):
    viewer = Viewer(Config(Session(StoredComms({"python_enumeration": not value})), exclude_keys=()))
    viewer.config.set_defaults(python_enumeration=value)
    boxes = [Pos(2 * i, 0, 0) * Box(1, 1, 1) for i in range(3)]
    viewer.show(*boxes, progress=None)
    assert viewer.last_paths == expected
    _assert_not_sent(viewer)
