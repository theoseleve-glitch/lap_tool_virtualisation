from __future__ import annotations

import argparse

from trackreco.config import load_config
from trackreco.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="TrackReco outdoor kart venue acquisition pipeline")
    parser.add_argument("--config", default="config/pipeline.json", help="Path to deterministic pipeline config")
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = run_pipeline(config)
    print(output_dir)


if __name__ == "__main__":
    main()
