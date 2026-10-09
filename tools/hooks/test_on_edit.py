"""Claude Code PostToolUse hook: after an Edit/Write to library, eval or test code, run the unit tests.

Exit code 2 feeds the failure back to the agent so it fixes the break immediately instead of
discovering it three edits later (or in a paid eval run).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCH = ("docext", "eval", "tests", "api")

try:
    payload = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)
path = Path(payload.get("tool_input", {}).get("file_path", ""))
try:
    rel = path.resolve().relative_to(ROOT)
except ValueError:
    sys.exit(0)
if rel.suffix != ".py" or rel.parts[0] not in WATCH:
    sys.exit(0)
py = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
r = subprocess.run([str(py if py.exists() else sys.executable), "-m", "pytest", "-q", "-x", "--no-header", "tests"],
                   cwd=ROOT, capture_output=True, text=True, timeout=300)
if r.returncode != 0:
    print(f"unit tests failed after editing {rel}:\n{r.stdout[-3000:]}", file=sys.stderr)
    sys.exit(2)
