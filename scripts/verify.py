"""Check compiled defaults and prove the regression test rejects the baseline."""
import json
from pathlib import Path
import re
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
results = Path(sys.argv[2]).resolve()
test = source / "test/parallel/test-buffer-gc-scavenger-default.js"
metadata = {}
for name, expected in (("baseline", 32), ("patched", 8)):
    binary = results / f"node-{name}"
    metadata[name] = json.loads(subprocess.check_output(
        [str(binary), "-p", "JSON.stringify({versions:process.versions,arch:process.arch,"
         "platform:process.platform,config:process.config.variables})"], text=True))
    for flags, value in (([], expected),
                         (["--scavenger-max-new-space-capacity-mb=32"], 32),
                         (["--scavenger-max-new-space-capacity-mb=4"], 4)):
        output = subprocess.check_output([str(binary), *flags, "--v8-options"], text=True)
        match = re.search(r"default: --scavenger-max-new-space-capacity-mb=(\d+)", output)
        if not match or int(match[1]) != value:
            raise RuntimeError(f"{name}: expected capacity {value}, flags={flags}")
    result = subprocess.run([str(binary), str(test)], capture_output=True, text=True)
    (results / f"regression-{name}.log").write_text(result.stdout + result.stderr)
    if name == "baseline":
        if result.returncode == 0 or "32 !== 8" not in result.stderr:
            raise RuntimeError("Baseline must reject the new default assertion")
    elif result.returncode != 0:
        raise RuntimeError(f"Patched regression test failed: {result.stderr}")
(results / "runtime-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print("PASS: baseline fails expected assertion; patched default and overrides pass")
