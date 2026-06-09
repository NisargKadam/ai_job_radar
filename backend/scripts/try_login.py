"""Open a headful browser to log into LinkedIn ONCE (manual login).

The session is saved in the persistent user-data-dir and reused by all future
runs. No password is ever stored by this app.

    cd backend
    ./.venv/bin/python scripts/try_login.py

Log in normally in the window that opens, then close the window when done.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.scraper.linkedin import open_for_login  # noqa: E402

if __name__ == "__main__":
    print("Opening LinkedIn login. Log in, then close the window...")
    open_for_login(max_wait_seconds=600)
    print("Done. Session saved.")
