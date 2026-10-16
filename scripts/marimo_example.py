import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    from ssb_timeseries.dataset import Dataset
    from ssb_timeseries.types import SeriesType

    from timeseriestest.ts_utils import (
        add_metadata_mapping,
        to_timeseries_dataframe,
    )

    return (
        Dataset,
        Path,
        SeriesType,
        add_metadata_mapping,
        mo,
        pd,
        to_timeseries_dataframe,
    )


@app.cell
def _(Path):
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_PATH = PROJECT_ROOT / "tests" / "data"

    SERIES_KEYS = ["selskap", "Serienavn", "ltid", "sek"]
    VALUE_COLUMNS = ["rente", "belop_50"]
    SEPARATOR = "."
    return DATA_PATH, SEPARATOR, SERIES_KEYS, VALUE_COLUMNS


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Read dataset
    """)
    return


@app.cell
def _(DATA_PATH, pd):
    df = pd.read_parquet(DATA_PATH / "randomized_data.parquet")
    df
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Transform to timeseries dataframe
    """)
    return


@app.cell
def _(SERIES_KEYS, VALUE_COLUMNS, df, to_timeseries_dataframe):
    ts_df = to_timeseries_dataframe(
        df,
        period_column="periode",
        series_keys=SERIES_KEYS,
        value_columns=VALUE_COLUMNS,
        time_format="%Y%m",
        frequency="M",
    )
    ts_df
    return (ts_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Create timeseries Dataset
    """)
    return


@app.cell
def _(
    Dataset,
    SEPARATOR,
    SERIES_KEYS,
    SeriesType,
    add_metadata_mapping,
    df,
    ts_df,
):
    ts_dataset = Dataset(
        name="mikrokv",
        data_type=SeriesType.simple(),
        data=ts_df,
        find_existing=False,
        attributes=[*SERIES_KEYS, "variable"],
        separator=SEPARATOR,
        dataset_tags={
            "frequency": "monthly",
            "description": "Monthly rente and belop_50 series",
            "source": "mikrokv",
        },
    )
    add_metadata_mapping(
        source_df=df,
        from_col="selskap",
        to_cols=["selskapsnavn"],
        target_dataset=ts_dataset,
    )
    ts_dataset.data
    return


if __name__ == "__main__":
    app.run()
