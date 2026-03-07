#!/usr/bin/env bash
set -euo pipefail
trackreco --config "${1:-config/pipeline.json}"
