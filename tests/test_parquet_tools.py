import json
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from timeseriestest.parquet_tools import parquet_to_text, text_to_parquet


def test_parquet_text_round_trip_preserves_data_and_schema(tmp_path: Path) -> None:
    schema = pa.schema(
        cast(
            "list[pa.Field[Any]]",
            [
                pa.field("count", pa.int32()),
                pa.field("when", pa.timestamp("us", tz="Europe/Oslo")),
                pa.field("label", pa.string()),
                pa.field("category", pa.dictionary(pa.int8(), pa.string())),
            ],
        ),
        metadata={b"source": b"round-trip-test"},
    )
    table = pa.Table.from_arrays(
        [
            pa.array([1, None, 3], type=pa.int32()),
            pa.array([0, 1_000_000, None], type=pa.timestamp("us", tz="Europe/Oslo")),
            pa.array(["", None, "quoted, value"]),
            pa.array(["a", "b", "a"])
            .dictionary_encode()
            .cast(pa.dictionary(pa.int8(), pa.string())),
        ],
        schema=schema,
    )
    source_file = tmp_path / "source.parquet"
    pq.write_table(table, source_file)

    data_file, metadata_file = parquet_to_text(source_file, tmp_path / "text")
    restored_file = text_to_parquet(tmp_path / "text", tmp_path / "restored")

    restored = pq.read_table(restored_file)
    assert data_file.name == "data.csv"
    assert metadata_file.name == "metadata.json"
    assert json.loads(metadata_file.read_text(encoding="utf-8"))["parquet_file"] == (
        source_file.name
    )
    assert restored_file.name == source_file.name
    assert restored.equals(table)
    assert restored.schema == table.schema
