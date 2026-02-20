from __future__ import annotations

import pandera as pa
from pandera import Check, Column


def schema() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "firm_id": Column(int, Check.ge(0), nullable=False),
            "year": Column(int, Check.between(2000, 2035), nullable=False),
            "x": Column(float, Check.isfinite(), nullable=False),
            "treat": Column(int, Check.isin([0, 1]), nullable=False),
            "y": Column(float, Check.isfinite(), nullable=False),
        },
        checks=[
            # (firm_id, year) 不能重复：这是面板数据最常见的 silent error 触发点之一
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