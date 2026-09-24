from pathlib import Path

import pandas as pd
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType

OUTPUT_PATH = Path(__file__).parent

# mikrokv_file = text_to_parquet(OUTPUT_PATH, OUTPUT_PATH)

mikrokv_df = pd.read_parquet(OUTPUT_PATH / "randomized_data.parquet")
mikrokv_df = mikrokv_df[
	["periode", "selskap", "Serienavn", "ltid", "sek", "rente", "belop_50"]
]


mikrokv_df["periode"] = pd.to_datetime(
	mikrokv_df["periode"], format="%Y%m"
).dt.to_period("M")

series_keys = ["selskap", "Serienavn", "ltid", "sek"]
timeseries_df = mikrokv_df.pivot(
	index="periode",
	columns=series_keys,
	values=["rente", "belop_50"],
)
timeseries_df = timeseries_df.reorder_levels(
	[1, 2, 3, 4, 0], axis="columns"
).sort_index(axis="columns")
timeseries_df.columns.names = [*series_keys, "variable"]

separator = "."
metadata_attributes = [*series_keys, "variable"]
dataset_df = timeseries_df.copy()
dataset_df.columns = [
	separator.join(str(part) for part in column) for column in dataset_df.columns
]
assert isinstance(dataset_df.index, pd.PeriodIndex)
dataset_df.index = dataset_df.index.to_timestamp("M")
dataset_df = dataset_df.rename_axis("valid_at").reset_index()

mikrokv_dataset = Dataset(
	name="mikrokv",
	data_type=SeriesType.simple(),
	data=dataset_df,
	find_existing=False,
	attributes=metadata_attributes,
	separator=separator,
	dataset_tags={
		"frequency": "monthly",
		"description": "Monthly rente and belop_50 series",
		"source": "mikrokv",
	},
)

rente_series = [
	name
	for name, tags in mikrokv_dataset.series_tags.items()
	if tags["variable"] == "rente"
]
belop_series = [
	name
	for name, tags in mikrokv_dataset.series_tags.items()
	if tags["variable"] == "belop_50"
]
mikrokv_dataset.tag_series(rente_series, tags={"unit": "percent"})
mikrokv_dataset.tag_series(belop_series, tags={"unit": "NOK"})

print(mikrokv_dataset)
print(mikrokv_dataset.data[["valid_at"]].head())
print(f"Number of series: {len(mikrokv_dataset.series)}")
print(mikrokv_dataset.series_tags[mikrokv_dataset.series[0]])





