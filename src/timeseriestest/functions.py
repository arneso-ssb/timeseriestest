"""A collection of useful functions."""

import base64
import json
from collections import defaultdict
from pathlib import Path
from typing import TypedDict, cast

import pandas as pd
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
from ssb_timeseries.dataset import Dataset

DATA_FILENAME = "data.csv"
METADATA_FILENAME = "metadata.json"


class _Manifest(TypedDict):
    format_version: int
    parquet_file: str
    schema: str
    arrow_schema: str


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
    for series_name, tags in target_dataset.series_tags.items():
        if from_col not in tags:
            raise KeyError(f"Series {series_name!r} has no {from_col!r} tag")
        series_by_key[str(tags[from_col])].append(series_name)

    unmapped_keys = sorted(set(series_by_key) - set(metadata_by_key))
    if unmapped_keys:
        raise ValueError(f"No metadata mapping found for {from_col}: {unmapped_keys}")

    for key, series_names in series_by_key.items():
        target_dataset.tag_series(series_names, tags=metadata_by_key[key])

    return target_dataset


def parquet_to_text(parquet_file: Path, output_directory: Path) -> tuple[Path, Path]:
    """Export a Parquet file as CSV data and a JSON schema manifest.

    Args:
        parquet_file: Parquet file to export.
        output_directory: Directory in which to create the text files.

    Returns:
        The paths of the CSV data file and JSON metadata file.
    """
    table = pq.read_table(parquet_file)
    output_directory.mkdir(parents=True, exist_ok=True)

    data_file = output_directory / DATA_FILENAME
    metadata_file = output_directory / METADATA_FILENAME
    csv.write_csv(table, data_file)
    metadata_file.write_text(
        json.dumps(
            {
                "format_version": 1,
                "parquet_file": parquet_file.name,
                "schema": str(table.schema),
                "arrow_schema": base64.b64encode(table.schema.serialize()).decode(
                    "ascii"
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return data_file, metadata_file


def text_to_parquet(text_directory: Path, output_directory: Path) -> Path:
    """Recreate a Parquet file from CSV data and a JSON schema manifest.

    Args:
        text_directory: Directory containing ``data.csv`` and ``metadata.json``.
        output_directory: Directory in which to create the Parquet file.

    Returns:
        The path of the recreated Parquet file.

    Raises:
        ValueError: If the manifest version or Parquet filename is invalid.
    """
    manifest = cast(
        _Manifest,
        json.loads((text_directory / METADATA_FILENAME).read_text(encoding="utf-8")),
    )
    if manifest["format_version"] != 1:
        msg = "Unsupported text transfer format version"
        raise ValueError(msg)

    parquet_name = manifest["parquet_file"]
    if Path(parquet_name).name != parquet_name:
        msg = "The manifest contains an invalid Parquet filename"
        raise ValueError(msg)

    schema = pa.ipc.read_schema(
        pa.py_buffer(base64.b64decode(manifest["arrow_schema"], validate=True))
    )
    csv_types = {
        field.name: field.type.value_type
        if pa.types.is_dictionary(field.type)
        else field.type
        for field in schema
    }
    table = csv.read_csv(
        text_directory / DATA_FILENAME,
        convert_options=csv.ConvertOptions(
            column_types=csv_types,
            strings_can_be_null=True,
            quoted_strings_can_be_null=False,
        ),
    )
    table = table.cast(schema)

    output_directory.mkdir(parents=True, exist_ok=True)
    parquet_file = output_directory / parquet_name
    pq.write_table(table, parquet_file)
    return parquet_file


def example_function(number1: int, number2: int) -> str:
    """Compare two integers.

    This is merely an example function can be deleted. It is used to show and test generating
    documentation from code, type hinting, testing, and testing examples
    in the code.


    Args:
        number1: The first number.
        number2: The second number, which will be compared to number1.

    Returns:
        A string describing which number is the greatest.

    Examples:
        Examples should be written in doctest format, and should illustrate how
        to use the function.

        >>> example_function(1, 2)
        1 is less than 2

    """
    if number1 < number2:
        return f"{number1} is less than {number2}"

    return f"{number1} is greater than or equal to {number2}"
