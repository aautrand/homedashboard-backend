import os
import subprocess
from typing import Any, Dict

from matplotlib import pyplot as plt


def _get(d: Dict, *keys) -> Any:
    for k in keys:
        d = d.get(k, {})
    return d.get("value") if isinstance(d, dict) else None


def latex_to_png(
    expr: str,
    number: int,
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
    text = f"{number}. ${expr}$"
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
    subprocess.run(cmd, check=True)
    delete_files(files)
