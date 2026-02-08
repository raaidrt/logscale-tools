"""Custom hatch build hook that downloads and bundles the topiary CLI binary."""

from __future__ import annotations

import io
import platform
import shutil
import stat
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

TOPIARY_VERSION = "v0.7.3"
TOPIARY_BASE_URL = (
    f"https://github.com/tweag/topiary/releases/download/{TOPIARY_VERSION}"
)

PLATFORM_MAP: dict[tuple[str, str], str] = {
    ("Darwin", "arm64"): "topiary-cli-aarch64-apple-darwin.tar.xz",
    ("Darwin", "x86_64"): "topiary-cli-x86_64-apple-darwin.tar.xz",
    ("Linux", "aarch64"): "topiary-cli-aarch64-unknown-linux-gnu.tar.xz",
    ("Linux", "x86_64"): "topiary-cli-x86_64-unknown-linux-gnu.tar.xz",
    ("Windows", "AMD64"): "topiary-cli-x86_64-pc-windows-msvc.zip",
}


def _get_asset_name() -> str:
    system = platform.system()
    machine = platform.machine()
    key = (system, machine)
    if key not in PLATFORM_MAP:
        raise RuntimeError(
            f"Unsupported platform: {system} {machine}. "
            f"Supported platforms: {list(PLATFORM_MAP.keys())}"
        )
    return PLATFORM_MAP[key]


def _download_topiary(dest_dir: Path) -> Path:
    """Download and extract the topiary binary into dest_dir."""
    asset_name = _get_asset_name()
    url = f"{TOPIARY_BASE_URL}/{asset_name}"

    print(f"Downloading topiary {TOPIARY_VERSION} from {url}")
    response = urllib.request.urlopen(url)  # noqa: S310
    data = response.read()

    # The binary inside the archive is named "topiary" (or "topiary.exe" on Windows)
    archive_binary = "topiary.exe" if platform.system() == "Windows" else "topiary"
    dest_binary = archive_binary
    dest_dir.mkdir(parents=True, exist_ok=True)

    if asset_name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for member in zf.namelist():
                if member.endswith(archive_binary):
                    extracted = dest_dir / dest_binary
                    extracted.write_bytes(zf.read(member))
                    break
            else:
                raise RuntimeError(f"{archive_binary} not found in {asset_name}")
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tf:
            for member in tf.getmembers():
                if member.name.endswith(f"/{archive_binary}"):
                    f = tf.extractfile(member)
                    if f is None:
                        raise RuntimeError(f"Could not extract {member.name}")
                    extracted = dest_dir / dest_binary
                    extracted.write_bytes(f.read())
                    break
            else:
                raise RuntimeError(f"{archive_binary} not found in {asset_name}")

    binary_path = dest_dir / dest_binary
    binary_path.chmod(binary_path.stat().st_mode | stat.S_IEXEC)
    return binary_path


class TopiariBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:  # type: ignore[type-arg]
        """Download topiary and include it in the wheel."""
        bin_dir = Path(self.root) / "src" / "logscale_query_language" / "bin"

        # Check if topiary is already downloaded
        binary_name = "topiary.exe" if platform.system() == "Windows" else "topiary"
        binary_path = bin_dir / binary_name
        if not binary_path.exists():
            _download_topiary(bin_dir)

        # Include the binary in the wheel
        build_data["force_include"][str(bin_dir)] = "logscale_query_language/bin"

    def clean(self, versions: list[str]) -> None:
        """Remove downloaded topiary binary."""
        bin_dir = Path(self.root) / "src" / "logscale_query_language" / "bin"
        if bin_dir.exists():
            shutil.rmtree(bin_dir)
            print(f"Cleaned {bin_dir}")
