"""save_screenshot polls for the file until `timeout_s` runs out, whole or fractional."""

import time

import pytest
from ocp_viewer_core.comms import Comms, Session
from ocp_viewer_core.config import Config
from ocp_viewer_core.show import Viewer


class ScreenshotComms(Comms[None]):
    """A viewer that writes the screenshot when asked, or never does."""

    def __init__(self, writes):
        super().__init__()
        self.writes = writes

    def send_command(self, data, timeit=False):
        if self.writes:
            with open(data["filename"], "wb") as f:
                f.write(b"png")


def _viewer(writes):
    return Viewer(Config(Session(ScreenshotComms(writes)), exclude_keys=()))


@pytest.mark.parametrize("timeout_s", [0.3, 1])
def test_a_missing_file_waits_timeout_s_and_says_so(tmp_path, capsys, timeout_s):
    start = time.monotonic()
    _viewer(writes=False).save_screenshot(str(tmp_path / "shot.png"), timeout_s=timeout_s)
    elapsed = time.monotonic() - start
    assert timeout_s <= elapsed < timeout_s + 0.5
    assert f"not found in {timeout_s} seconds" in capsys.readouterr().out


def test_a_written_file_is_reported_at_once(tmp_path, capsys):
    target = tmp_path / "shot.png"
    start = time.monotonic()
    _viewer(writes=True).save_screenshot(str(target), timeout_s=5)
    assert time.monotonic() - start < 1
    assert f"Screenshot saved to  {target}" in capsys.readouterr().out


def test_progress_only_keeps_its_position(tmp_path, capsys):
    # filename, port, polling, progress_only - the order before timeout_s existed
    _viewer(writes=True).save_screenshot(str(tmp_path / "shot.png"), None, True, True)
    assert capsys.readouterr().out == "."
