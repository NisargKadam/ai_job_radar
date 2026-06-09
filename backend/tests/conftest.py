import os
import pathlib
import tempfile

# Default every test run at a throwaway DB so we never touch the real aijr.db.
# Individual tests may override AIJR_DB_URL via monkeypatch and call init_db().
_tmp = pathlib.Path(tempfile.gettempdir()) / "aijr_pytest.db"
if _tmp.exists():
    _tmp.unlink()
os.environ["AIJR_DB_URL"] = f"sqlite:///{_tmp}"
