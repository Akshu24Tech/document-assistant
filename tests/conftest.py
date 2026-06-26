import os
import tempfile

# config requires a key on import, and the history db / chroma dir should land
# somewhere disposable during tests — set all of that before app code loads.
os.environ.setdefault("GEMINI_API_KEY", "test-key")

_tmp = tempfile.mkdtemp(prefix="docassist-test-")
os.environ.setdefault("CHROMA_DIR", os.path.join(_tmp, "chroma"))
os.environ.setdefault("HISTORY_DB", os.path.join(_tmp, "history.db"))
