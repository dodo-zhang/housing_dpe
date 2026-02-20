from __future__ import annotations

import argparse
from pathlib import Path

from housing_dpe.pipeline import run


def main():
    p = argparse.ArgumentParser(prog="housing_dpe")
    p.add_argument("--config", type=Path, default=Path("config/params.yaml"))
    p.add_argument("--outdir", type=Path, default=Path("outputs"))
    args = p.parse_args()
    run(args.config, args.outdir)


if __name__ == "__main__":
    main()