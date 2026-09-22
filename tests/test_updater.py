from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.version import APP_VERSION
from core.updater import UpdateInfo, find_latest_beta_release, is_newer_version


def test_current_version_is_beta():
    assert APP_VERSION == "0.1.3-beta"


def test_newer_version_comparison():
    assert is_newer_version("0.1.4-beta", "0.1.3-beta")
    assert not is_newer_version("0.1.3-beta", "0.1.3-beta")
    assert not is_newer_version("0.1.2-beta", "0.1.3-beta")


def test_find_latest_beta_release_with_installer():
    releases = [
        {"tag_name": "v0.1.4-beta", "draft": False, "html_url": "https://github.com/joaofoguin/music-karaoke-player/releases/tag/v0.1.4-beta", "assets": [{"name": "StageBox-Beta-Setup.exe", "browser_download_url": "https://github.com/joaofoguin/music-karaoke-player/releases/download/v0.1.4-beta/StageBox-Beta-Setup.exe"}]},
        {"tag_name": "v0.1.5-beta", "draft": True, "html_url": "", "assets": [{"name": "StageBox-Beta-Setup.exe", "browser_download_url": "https://github.com/joaofoguin/music-karaoke-player/releases/download/v0.1.5-beta/StageBox-Beta-Setup.exe"}]},
        {"tag_name": "v0.1.4", "draft": False, "html_url": "", "assets": [{"name": "StageBox-Beta-Setup.exe", "browser_download_url": "https://github.com/joaofoguin/music-karaoke-player/releases/download/v0.1.4/StageBox-Beta-Setup.exe"}]},
    ]
    result = find_latest_beta_release(releases)
    assert isinstance(result, UpdateInfo)
    assert result.version == "0.1.4-beta"
    assert result.installer_url.endswith("StageBox-Beta-Setup.exe")
