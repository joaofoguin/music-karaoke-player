import json
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .version import APP_VERSION

GITHUB_API_URL = "https://api.github.com/repos/joaofoguin/music-karaoke-player/releases"
INSTALLER_NAME = "StageBox-Beta-Setup.exe"


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    release_url: str
    installer_url: str


def _version_key(version: str):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?", version.strip())
    if not match:
        raise ValueError(f"Versão inválida: {version}")
    major, minor, patch = (int(match.group(i)) for i in range(1, 4))
    prerelease = match.group(4)
    return major, minor, patch, 0 if prerelease else 1, prerelease or ""


def is_newer_version(candidate: str, current: str = APP_VERSION) -> bool:
    try:
        return _version_key(candidate) > _version_key(current)
    except ValueError:
        return False


def _fetch_releases(url: str = GITHUB_API_URL):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "StageBox-Updater"},
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def find_latest_beta_release(releases) -> UpdateInfo | None:
    candidates = []
    for release in releases:
        tag = str(release.get("tag_name", ""))
        if not tag.lower().endswith("-beta") or release.get("draft"):
            continue

        installer_url = next(
            (asset.get("browser_download_url") for asset in release.get("assets", [])
             if asset.get("name") == INSTALLER_NAME),
            None,
        )
        if installer_url and is_newer_version(tag):
            candidates.append(UpdateInfo(
                version=tag.lstrip("v"),
                release_url=str(release.get("html_url", "")),
                installer_url=str(installer_url),
            ))

    return max(candidates, key=lambda item: _version_key(item.version)) if candidates else None


def check_for_update() -> UpdateInfo | None:
    try:
        return find_latest_beta_release(_fetch_releases())
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def download_installer(installer_url: str) -> Path:
    parsed = urllib.parse.urlparse(installer_url)
    if parsed.scheme != "https" or not (
        parsed.netloc == "github.com" or parsed.netloc.endswith(".github.com")
    ):
        raise ValueError("URL de atualização não autorizada")

    destination = Path(tempfile.gettempdir()) / INSTALLER_NAME
    request = urllib.request.Request(installer_url, headers={"User-Agent": "StageBox-Updater"})
    with urllib.request.urlopen(request, timeout=30) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
    return destination


def open_installer(path: Path) -> None:
    subprocess.Popen([str(path)], close_fds=True)


class UpdateChecker(QThread):
    update_available = Signal(object)

    def run(self):
        update = check_for_update()
        if update is not None:
            self.update_available.emit(update)
