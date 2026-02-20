from __future__ import annotations

import numpy as np
import pandera.pandas as pa
from pandera.pandas import Check, Column


def _is_finite() -> Check:
    # Compatible across pandera versions: don't rely on Check.isfinite()
    return Check(lambda s: np.isfinite(s).all(), error="non-finite values detected")


def schema() -> pa.DataFrameSchema:
    finite = _is_finite()

    return pa.DataFrameSchema(
        {
            "firm_id": Column(int, Check.ge(0), nullable=False),
            "year": Column(int, Check.between(2000, 2035), nullable=False),
            "x": Column(float, finite, nullable=False),
            "treat": Column(int, Check.isin([0, 1]), nullable=False),
            "y": Column(float, finite, nullable=False),
        },
        checks=[
            Check(
                lambda df: (~df[["firm_id", "year"]].duplicated()).all(),
                error="Duplicate (firm_id, year) detected.",
            ),
            Check(lambda df: len(df) > 0, error="Empty dataframe."),
        ],
        coerce=True,
        strict=True,
    )


def validate_df(df):
    return schema().validate(df, lazy=True)
