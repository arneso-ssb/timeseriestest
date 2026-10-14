"""Utilities for working with time-series datasets."""

from collections import defaultdict
from typing import cast

import pandas as pd
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import TagDict


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


def add_metadata_mapping(
    source_df: pd.DataFrame,
    from_col: str,
    to_cols: list[str],
    target_dataset: Dataset,
) -> Dataset:
    """Add metadata attributes to series using a source-column mapping.

    Args:
        source_df: Data containing the mapping attributes.
        from_col: Source column matching an existing series tag.
        to_cols: Source columns to add as series metadata.
        target_dataset: Dataset whose series metadata will be updated.

    Returns:
        The updated dataset. The input dataset is modified in place.

    Raises:
        KeyError: If a required source column or series tag is missing.
        ValueError: If columns contain nulls, a source key maps to conflicting
            metadata, or a series key has no source mapping.
    """
    if not to_cols:
        raise ValueError("to_cols must contain at least one column")
    if from_col in to_cols or len(to_cols) != len(set(to_cols)):
        raise ValueError("from_col and to_cols must contain distinct columns")

    required_columns = [from_col, *to_cols]
    missing_columns = set(required_columns) - set(source_df.columns)
    if missing_columns:
        raise KeyError(f"Source columns not found: {sorted(missing_columns)}")

    mapping_rows = source_df[required_columns].drop_duplicates()
    if mapping_rows.isna().any(axis=None):
        raise ValueError("Metadata mapping columns must not contain null values")

    conflicting = mapping_rows[from_col].duplicated(keep=False)
    if conflicting.any():
        conflicting_keys = sorted(mapping_rows.loc[conflicting, from_col].astype(str))
        raise ValueError(
            f"Values in {from_col!r} map to conflicting metadata: {conflicting_keys}"
        )

    metadata_by_key = {
        str(values[0]): dict(
            zip(to_cols, (str(value) for value in values[1:]), strict=True)
        )
        for values in mapping_rows.itertuples(index=False, name=None)
    }

    series_by_key: dict[str, list[str]] = defaultdict(list)
    # Remove this cast when https://github.com/statisticsnorway/ssb-timeseries/issues/267 is fixed.
    series_tags = cast(dict[str, TagDict], target_dataset.series_tags)
    for series_name, tags in series_tags.items():
        if from_col not in tags:
            raise KeyError(f"Series {series_name!r} has no {from_col!r} tag")
        series_by_key[str(tags[from_col])].append(series_name)

    unmapped_keys = sorted(set(series_by_key) - set(metadata_by_key))
    if unmapped_keys:
        raise ValueError(f"No metadata mapping found for {from_col}: {unmapped_keys}")

    for key, series_names in series_by_key.items():
        target_dataset.tag_series(series_names, tags=metadata_by_key[key])

    return target_dataset
