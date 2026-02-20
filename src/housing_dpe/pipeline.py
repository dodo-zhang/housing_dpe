from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

from housing_dpe.validate import validate_df


@dataclass(frozen=True)
class Params:
    seed: int
    n_rows: int
    formula: str
    cov_type: str


def load_params(path: Path) -> Params:
    obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Params(
        seed=int(obj["seed"]),
        n_rows=int(obj["n_rows"]),
        formula=str(obj["model"]["formula"]),
        cov_type=str(obj["model"]["cov_type"]),
    )


def generate_synthetic_panel(n_rows: int, seed: int) -> pd.DataFrame:
    """
    Synthetic panel data with a known treatment effect.
    目的：让模板项目无需外部数据就能一键跑通+可测试。
    """
    rng = np.random.default_rng(seed)
    n_firms = max(50, int(np.sqrt(n_rows)))
    years = np.arange(2010, 2021)

    firm_id = rng.integers(0, n_firms, size=n_rows)
    year = rng.choice(years, size=n_rows, replace=True)

    # covariate
    x = rng.normal(0, 1, size=n_rows)

    # treatment assignment with firm heterogeneity (still synthetic)
    p = 1 / (1 + np.exp(-(0.3 * x + (firm_id % 7 - 3) * 0.2)))
    treat = (rng.uniform(0, 1, size=n_rows) < p).astype(int)

    true_tau = 0.5
    firm_fe = (firm_id % 10 - 5) * 0.05
    year_fe = (year - year.mean()) * 0.02
    eps = rng.normal(0, 1.0, size=n_rows)

    y = true_tau * treat + 0.8 * x + firm_fe + year_fe + eps

    df = pd.DataFrame(
        {"firm_id": firm_id, "year": year, "x": x, "treat": treat, "y": y}
    )

    # enforce unique (firm_id, year) by aggregating if needed
    # （真实研究你会在 merge 前做；这里为了模板稳健性）
    df = (
        df.groupby(["firm_id", "year"], as_index=False)
        .agg({"x": "mean", "treat": "max", "y": "mean"})
        .sort_values(["firm_id", "year"])
        .reset_index(drop=True)
    )
    return df


def estimate(df: pd.DataFrame, formula: str, cov_type: str):
    model = smf.ols(formula, data=df).fit()
    if cov_type == "cluster":
        # statsmodels 支持 clustered covariance（groups 必填）
        res = model.get_robustcov_results(cov_type="cluster", groups=df["firm_id"])
        return res
    return model.get_robustcov_results(cov_type=cov_type)


def save_outputs(outdir: Path, df: pd.DataFrame, res) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "tables").mkdir(exist_ok=True)
    (outdir / "figures").mkdir(exist_ok=True)
    (outdir / "logs").mkdir(exist_ok=True)

    df.to_csv(outdir / "data_processed.csv", index=False)

    # Table
    tbl = res.summary2().tables[1].copy()
    tbl.to_csv(outdir / "tables" / "regression.csv")

    # Also export LaTeX for papers
    (outdir / "tables" / "regression.tex").write_text(
        tbl.to_latex(float_format="%.4f"), encoding="utf-8"
    )

    # Try to recover parameter names
    param_names = None
    for attr in ("model",):
        if hasattr(res, attr) and hasattr(getattr(res, attr), "exog_names"):
            param_names = getattr(res, attr).exog_names
            break
    if (
        param_names is None
        and hasattr(res, "model")
        and hasattr(res.model, "data")
        and hasattr(res.model.data, "param_names")
    ):
        param_names = res.model.data.param_names

    def _get_param_idx(name: str) -> int:
        if param_names and name in param_names:
            return param_names.index(name)
        # Fallback: assume treat is the 2nd regressor after intercept in "y ~ treat + ..."
        # This is a safe fallback for our template, but in real research you'd enforce name presence.
        return 1

    idx = _get_param_idx("treat")

    params = np.asarray(res.params)
    bse = np.asarray(res.bse)

    coef = float(params[idx])
    se = float(bse[idx])
    ci_low, ci_high = coef - 1.96 * se, coef + 1.96 * se

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.errorbar([0], [coef], yerr=[[coef - ci_low], [ci_high - coef]], fmt="o")
    ax.axhline(0, linestyle="--")
    ax.set_xticks([0])
    ax.set_xticklabels(["treat"])
    ax.set_title("Treatment effect (coef ± 1.96*SE)")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "treat_effect.png", dpi=200)
    plt.close(fig)
    ci_low, ci_high = coef - 1.96 * se, coef + 1.96 * se

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.errorbar([0], [coef], yerr=[[coef - ci_low], [ci_high - coef]], fmt="o")
    ax.axhline(0, linestyle="--")
    ax.set_xticks([0])
    ax.set_xticklabels(["treat"])
    ax.set_title("Treatment effect (coef ± 1.96*SE)")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "treat_effect.png", dpi=200)
    plt.close(fig)

    # Metadata log
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": safe_git_commit(),
        "n_obs": int(len(df)),
    }
    (outdir / "logs" / "run_metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )


def safe_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def run(config_path: Path, outdir: Path) -> None:
    params = load_params(config_path)

    df = generate_synthetic_panel(params.n_rows, params.seed)
    df = validate_df(df)

    res = estimate(df, params.formula, params.cov_type)
    save_outputs(outdir, df, res)


if __name__ == "__main__":
    run(Path("config/params.yaml"), Path("outputs"))
