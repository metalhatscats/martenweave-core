#!/usr/bin/env bash
# Build the Workbench and copy the exact production assets into package data.
# `martenweave workbench` uses these assets when frontend/dist is unavailable,
# which is the normal case for an installed wheel.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
frontend_dir="$repo_root/frontend"
package_dir="$repo_root/src/modelops_core/workbench_static"

npm --prefix "$frontend_dir" run build

rm -rf "$package_dir"
mkdir -p "$package_dir"
cp -R "$frontend_dir/dist/." "$package_dir/"
# Design-QA reference screenshots are development artifacts; never ship them in
# the packaged workbench assets (they bloat the wheel by several MB).
rm -rf "$package_dir/qa"
