import hashlib
import json
import os
import subprocess  # nosec B404
from typing import Any, Dict

from matplotlib import pyplot as plt


def env_flag(name: str, default: bool = True) -> bool:
    """Read a boolean env var, treating 0/false/no/off as off."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off")


def _get(d: Dict, *keys) -> Any:
    for k in keys:
        d = d.get(k, {})
    return d.get("value") if isinstance(d, dict) else None


def latex_to_png(
    expr: str,
    filename: str,
    fontsize: int = 20,
    dpi: int = 300,
    pad_inches: float = 0.05,
):
    """
    Render a single numbered LaTeX expression to a tightly-cropped PNG.

    - expr: bare LaTeX (no $…$).
    - number: the problem index, to prefix before the formula.
    - filename: output path, e.g. "item_01.png"
    - fontsize, dpi: keep these the same for all images!
    - pad_inches: extra whitespace around the box.
    """
    fig = plt.figure(figsize=(2, 2), dpi=dpi)
    fig.patch.set_facecolor("white")

    # Prefix the number outside math mode, then the formula in math mode
    text = f"${expr}$"
    fig.text(0, 0, text, fontsize=fontsize, ha="left", va="bottom")

    # draw & tightly crop
    fig.canvas.draw()
    fig.savefig(
        filename, dpi=dpi, bbox_inches="tight", pad_inches=pad_inches, transparent=False
    )
    plt.close(fig)


def delete_files(files):
    for path in files:
        try:
            os.remove(path)
            print(f"Deleted: {path}")
        except FileNotFoundError:
            print(f"Not found: {path}")
        except PermissionError:
            print(f"Permission denied: {path}")
        except OSError as e:
            print(f"Error deleting {path}: {e}")


def scp_files(
    files,
    user,
    destination_host,
    destination_path,
    key_path="~/.ssh/id_printer_ed25519",
):
    # expand ~ in key_path
    key_path = os.path.expanduser(key_path)

    # build target and base cmd
    target = f"{user}@{destination_host}:{destination_path}"
    cmd = ["scp", "-i", key_path, "-o", "IdentitiesOnly=yes", *files, target]

    # run and then delete
    subprocess.run(cmd, check=True)  # nosec B603
    delete_files(files)


def get_version():
    from pathlib import Path

    # If you want it relative to this script file:
    current_dir = Path(__file__).resolve().parent
    print(current_dir)
    # Navigate three directories up (parents[0] is one up, parents[2] is three up)
    target_file = current_dir.parents[2] / "version"
    print(target_file)
    print("Looking for:", target_file)
    if target_file.exists():
        content = target_file.read_text().strip()
        return content
    else:
        print("File not found!")


def get_hash(obj):
    normalized = json.dumps(obj, sort_keys=True, separators=(",", ";"))
    return hashlib.sha256(normalized.encode()).hexdigest()
