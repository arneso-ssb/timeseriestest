"""Tools for transferring Parquet data through text files."""

import base64
import json
from pathlib import Path
from typing import TypedDict, cast

import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq

DATA_FILENAME = "data.csv"
METADATA_FILENAME = "metadata.json"


class _Manifest(TypedDict):
    format_version: int
    parquet_file: str
    schema: str
    arrow_schema: str


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
