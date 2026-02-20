from pathlib import Path
from housing_dpe.pipeline import run


def test_pipeline_smoke(tmp_path: Path):
    # use default config but write outputs into temp dir
    run(Path("config/params.yaml"), tmp_path)

    assert (tmp_path / "data_processed.csv").exists()
    assert (tmp_path / "tables" / "regression.csv").exists()
    assert (tmp_path / "figures" / "treat_effect.png").exists()
    assert (tmp_path / "logs" / "run_metadata.json").exists()
