#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
mkdir -p results
if [[ -e node-source ]]; then
  echo 'node-source already exists; use a fresh directory for reproducible builds.' >&2
  exit 1
fi
git init node-source
git -C node-source remote add origin https://github.com/nodejs/node.git
git -C node-source fetch --depth=1 origin 0d10bfe3cb961ef997490f5c060bd1466b5affea
git -C node-source checkout --detach FETCH_HEAD
cd node-source
./configure 2>&1 | tee ../results/configure.log
make -j "${JOBS:-4}" 2>&1 | tee ../results/build-baseline.log
cp out/Release/node ../results/node-baseline
git apply --check ../patches/node24-scavenger-default.patch
git apply ../patches/node24-scavenger-default.patch
make -j "${JOBS:-4}" 2>&1 | tee ../results/build-patched.log
cp out/Release/node ../results/node-patched
cp LICENSE ../results/LICENSE.node
sha256sum ../results/node-baseline ../results/node-patched > ../results/SHA256SUMS
