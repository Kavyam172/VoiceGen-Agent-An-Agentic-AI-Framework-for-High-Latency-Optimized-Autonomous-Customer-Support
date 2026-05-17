"""
run.py — Unified project launcher.

Provides a single entry point for running either the Streamlit UI or the
CLI mode, selectable via a command-line flag.

Usage
-----
    # Launch Streamlit UI (default)
    python run.py

    # Launch CLI interactive mode
    python run.py --cli

    # Launch CLI with debug output
    python run.py --cli --debug
"""

import os
import sys
import subprocess
from pathlib import Path

# run.py lives at customer_support_agent/run.py — resolve once, use everywhere.
_PROJECT_ROOT = Path(__file__).resolve().parent


def launch_streamlit() -> None:
    """Start the Streamlit application."""
    app_path = _PROJECT_ROOT / "streamlit_app" / "app.py"
    print(f"\n🚀 Starting Streamlit app: {app_path}\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=false",
        ],
        # Set cwd to the project root so the subprocess inherits the correct
        # working directory — this ensures load_dotenv() and relative paths
        # inside the app resolve against customer_support_agent/.
        cwd=str(_PROJECT_ROOT),
        check=True,
    )


def launch_cli() -> None:
    """Start the interactive CLI runner."""
    # Anchor CWD and sys.path so all imports resolve correctly.
    os.chdir(_PROJECT_ROOT)
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))

    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")

    from app.main import run_cli
    run_cli()


def main() -> None:
    if "--cli" in sys.argv:
        launch_cli()
    else:
        launch_streamlit()


if __name__ == "__main__":
    main()
