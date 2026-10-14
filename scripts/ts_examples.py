from pathlib import Path
from typing import cast

import pandas as pd
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType, TagDict

from timeseriestest.ts_utils import add_metadata_mapping, to_timeseries_dataframe

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "tests" / "data"

SERIES_KEYS = ["selskap", "Serienavn", "ltid", "sek"]
VALUE_COLUMNS = ["rente", "belop_50"]
SEPARATOR = "."


def main() -> None:
    """Build and save a time-series dataset from the example Parquet data."""
    print("Starting to process mikrokv data...")

    mikrokv_df = pd.read_parquet(DATA_PATH / "randomized_data.parquet")
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

    print(mikrokv_dataset.data[["valid_at"]].head())
    print(f"Number of series: {len(mikrokv_dataset.series)}")
    print(series_tags[mikrokv_dataset.series[0]])

    mikrokv_dataset.save()
    mikrokv_dataset.snapshot()
    print("Dataset saved and snapshot created.")


if __name__ == "__main__":
    main()
