"""Interleaved same-source baseline/patched measurements, with all raw samples."""
import argparse
import json
from pathlib import Path
import re
import statistics
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("results", type=Path)
parser.add_argument("--runs", type=int, default=7)
args = parser.parse_args()
source, results = args.source.resolve(), args.results.resolve()
samples = []
summary = {}
for workload in ("stream-burst", "buffer-churn", "buffer-retained", "heap-churn"):
    for run in range(args.runs):
        for name in (("baseline", "patched") if run % 2 == 0 else ("patched", "baseline")):
            binary = results / f"node-{name}"
            if workload == "stream-burst":
                command = [str(binary), str(source / "benchmark/streams/readable-push-buffer-burst-minimal.js"),
                           "n=20000", "bodySize=122880"]
            else:
                command = [str(binary), str(Path(__file__).with_name("workload.cjs")), workload]
            result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=True)
            if workload == "stream-burst":
                match = re.search(r": ([\d,.]+)\s*$", result.stdout)
                if not match:
                    raise RuntimeError(result.stdout + result.stderr)
                data = {"ops": float(match[1].replace(",", ""))}
            else:
                data = json.loads(result.stdout)
            samples.append({"workload": workload, "binary": name, "run": run, **data,
                            "stdout": result.stdout, "stderr": result.stderr})
            (results / "samples.json").write_text(json.dumps(samples, indent=2) + "\n")
    medians = {name: statistics.median(s["ops"] for s in samples
               if s["workload"] == workload and s["binary"] == name)
               for name in ("baseline", "patched")}
    summary[workload] = {**medians,
                         "median_change_percent": 100 * (medians["patched"] / medians["baseline"] - 1)}
    print(workload, summary[workload], flush=True)
(results / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
for name in ("baseline", "patched"):
    result = subprocess.run([str(results / f"node-{name}"), "--trace-gc",
        str(source / "benchmark/streams/readable-push-buffer-burst-minimal.js"),
        "n=20000", "bodySize=122880"], capture_output=True, text=True, timeout=180, check=True)
    (results / f"gc-{name}.log").write_text(result.stdout + result.stderr)
