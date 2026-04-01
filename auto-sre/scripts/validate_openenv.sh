#!/usr/bin/env bash
# Validate the environment against the OpenEnv specification.
set -euo pipefail

echo "Running OpenEnv validation..."
openenv validate --url http://localhost:8000
echo "Validation complete."
