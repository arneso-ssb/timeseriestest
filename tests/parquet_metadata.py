from pathlib import Path
from typing import cast

import pandas as pd
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType, TagDict

# from fagfunksjoner.log.statlogger import StatLogger
# from timeseriestest.functions import text_to_parquet
from timeseriestest import add_metadata_mapping

OUTPUT_PATH = Path(__file__).parent
SERIES_KEYS = ["selskap", "Serienavn", "ltid", "sek"]
VALUE_COLUMNS = ["rente", "belop_50"]
SEPARATOR = "."


def to_timeseries_dataframe(
    df: pd.DataFrame,
    period_column: str,
    time_format: str,
    frequency: str,
    series_keys: list[str],
    value_columns: list[str],
    separator: str = ".",
) -> pd.DataFrame:
    """Convert a long format dataset a to timeseries dataset.

    Each output series is named by joining its series-key values and source
    value-column name. The period column is converted to a ``valid_at`` timestamp
    column at the end of each period.

    Args:
        df: Source observations with one row per period and series-key combination.
        period_column: Name of the column containing the observation periods.
        time_format: Format used to parse the period values. Example: "%Y%m".
        frequency: Pandas frequency alias defining the period resolution. Example: "M" for monthly periods.
        series_keys: Columns whose values identify an individual series.
        value_columns: Columns containing the observations to turn into series.
        separator: Text used to join the parts of each output series name. Default is `.`.

    Returns:
        A timeseries DataFrame containing ``valid_at`` and one column per series.

    Raises:
        ValueError: If a period and series-key combination occurs more than once.

    """
    data = df[[period_column, *series_keys, *value_columns]].copy()
    if data.duplicated(subset=[period_column, *series_keys]).any():
        raise ValueError("Data contains duplicate rows")

    data[period_column] = pd.to_datetime(
        data[period_column], format=time_format
    ).dt.to_period(frequency)

    dataset_df = data.pivot(
        index=period_column,
        columns=series_keys,
        values=value_columns,
    )

    # Flatten the column names and make the value column the last one
    dataset_df.columns = [
        separator.join(str(part) for part in (*column[1:], column[0]))
        for column in dataset_df.columns
    ]
    assert isinstance(dataset_df.index, pd.PeriodIndex)
    dataset_df.index = dataset_df.index.to_timestamp(frequency)

    # the ssb-timeseries library expects the time index to be a column named "valid_at"
    return dataset_df.rename_axis("valid_at").reset_index()


def main() -> None:
    print("Starting to process mikrokv data...")

    mikrokv_df = pd.read_parquet(OUTPUT_PATH / "randomized_data.parquet")
    dataset_df = to_timeseries_dataframe(
        mikrokv_df,
        period_column="periode",
        series_keys=SERIES_KEYS,
        value_columns=VALUE_COLUMNS,
        time_format="%Y%m",
        frequency="M",
    )

    mikrokv_dataset = Dataset(
        name="mikrokv",
        data_type=SeriesType.simple(),
        data=dataset_df,
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
        source_df=mikrokv_df,
        from_col="selskap",
        to_cols=["selskapsnavn"],
        target_dataset=mikrokv_dataset,
    )

    # Remove this cast when https://github.com/statisticsnorway/ssb-timeseries/issues/267 is fixed.
    series_tags = cast(dict[str, TagDict], mikrokv_dataset.series_tags)
    rente_series = [
        name for name, tags in series_tags.items() if tags["variable"] == "rente"
    ]
    belop_series = [
        name for name, tags in series_tags.items() if tags["variable"] == "belop_50"
    ]
    mikrokv_dataset.tag_series(rente_series, tags={"unit": "percent"})
    mikrokv_dataset.tag_series(belop_series, tags={"unit": "NOK"})

    # print(mikrokv_dataset)
    print(mikrokv_dataset.data[["valid_at"]].head())
    print(f"Number of series: {len(mikrokv_dataset.series)}")
    print(series_tags[mikrokv_dataset.series[0]])


if __name__ == "__main__":
    # root_logger = StatLogger()
    # text_to_parquet(OUTPUT_PATH, OUTPUT_PATH)
    main()
