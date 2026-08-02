import os
import signal
import subprocess
import sys
import textwrap

import pytest


def test_dialog_can_be_created_and_destroyed():
    """Keep the legacy dialog traceable without risking the pytest process."""
    if sys.platform.startswith("linux") and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    ):
        pytest.skip("Tk requires DISPLAY or WAYLAND_DISPLAY on Linux")

    try:
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                textwrap.dedent(
                    """
                    import sys

                    try:
                        import tkinter as tk
                    except (ImportError, ModuleNotFoundError) as error:
                        print(f"Tk no disponible: {error}", file=sys.stderr)
                        raise SystemExit(77)

                    try:
                        root = tk.Tk()
                    except tk.TclError as error:
                        print(f"Tk sin display compatible: {error}", file=sys.stderr)
                        raise SystemExit(77)

                    root.withdraw()
                    try:
                        from ranges.dialog import RangesDialog
                        from ranges.manager import RangesManager

                        dialog = RangesDialog(root, RangesManager())
                        dialog.update_idletasks()
                        dialog.destroy()
                    finally:
                        root.destroy()
                    """
                ),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("El subproceso Tk no terminó en 15 segundos")

    detail = (probe.stderr or probe.stdout).strip()
    if probe.returncode == 77:
        pytest.skip(detail or "Tk no disponible en el entorno aislado")
    if probe.returncode < 0:
        try:
            reason = signal.Signals(-probe.returncode).name
        except ValueError:
            reason = f"signal {-probe.returncode}"
        pytest.skip(f"Tk abortó de forma nativa en el subproceso: {reason}")
    if probe.returncode != 0:
        pytest.fail(
            f"El diálogo Tk falló con código {probe.returncode}:\n"
            f"{detail or '(sin salida)'}"
        )
