import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType

from timeseriestest import add_metadata_mapping, parquet_to_text, text_to_parquet
from timeseriestest.functions import example_function


def _metadata_dataset() -> Dataset:
    return Dataset(
        name="metadata-test",
        data_type=SeriesType.simple(),
        data=pd.DataFrame(
            {
                "valid_at": pd.to_datetime(["2025-01-01"]),
                "001.rente": [1.0],
                "002.rente": [2.0],
            }
        ),
        find_existing=False,
        attributes=["selskap", "variable"],
        separator=".",
    )


def test_add_metadata_mapping_adds_multiple_attributes() -> None:
    source = pd.DataFrame(
        {
            "selskap": ["001", "001", "002"],
            "selskapsnavn": ["Company A", "Company A", "Company B"],
            "region": ["North", "North", "South"],
        }
    )
    dataset = _metadata_dataset()

    result = add_metadata_mapping(
        source,
        from_col="selskap",
        to_cols=["selskapsnavn", "region"],
        target_dataset=dataset,
    )

    assert result is dataset
    company_a_tags = cast(dict[str, str], result.series_tags["001.rente"])
    company_b_tags = cast(dict[str, str], result.series_tags["002.rente"])
    assert company_a_tags["selskapsnavn"] == "Company A"
    assert company_a_tags["region"] == "North"
    assert company_b_tags["selskapsnavn"] == "Company B"
    assert company_b_tags["region"] == "South"


def test_add_metadata_mapping_rejects_conflicting_mapping() -> None:
    source = pd.DataFrame(
        {
            "selskap": ["001", "001", "002"],
            "selskapsnavn": ["Company A", "Different name", "Company B"],
        }
    )

    with pytest.raises(ValueError, match="conflicting metadata"):
        add_metadata_mapping(
            source,
            from_col="selskap",
            to_cols=["selskapsnavn"],
            target_dataset=_metadata_dataset(),
        )


def test_example_function() -> None:
    assert example_function(1, 2) == "1 is less than 2"
    assert example_function(1, 0) == "1 is greater than or equal to 0"


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
