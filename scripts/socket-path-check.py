"""Separate Unix-domain socket path limits from a runtime regression."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

source, results = (Path(arg).resolve() for arg in sys.argv[1:])
records = []
for name in ("baseline", "patched"):
    for prefix, should_pass in (("n24-", True), ("n24-" + "x" * 90, False)):
        with tempfile.TemporaryDirectory(prefix=prefix, dir="/tmp") as test_root:
            for filename in ("test-fs-cp-async-socket.mjs", "test-fs-cp-sync-copy-socket-error.mjs"):
                result = subprocess.run(
                    [str(results / f"node-{name}"), str(source / "test/parallel" / filename)],
                    env={**os.environ, "NODE_TEST_DIR": test_root},
                    capture_output=True, text=True, timeout=30)
                records.append({"binary": name, "test": filename, "short_path": should_pass,
                                "exit_code": result.returncode, "stderr": result.stderr})
                if should_pass and result.returncode != 0:
                    raise RuntimeError(f"Short-path test failed: {name} {filename}\n{result.stderr}")
                if not should_pass and (result.returncode == 0 or
                                        not any(code in result.stderr for code in ("EINVAL", "ENOENT"))):
                    raise RuntimeError(f"Long-path negative control failed: {name} {filename}")
(results / "socket-path-controls.json").write_text(json.dumps(records, indent=2) + "\n")
print("PASS: both binaries reject oversized socket paths and pass with short paths")
