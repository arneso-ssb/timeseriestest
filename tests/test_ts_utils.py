from typing import Any, cast

import pandas as pd
import pytest
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType

from timeseriestest import (
    add_metadata_mapping,
    mapping_to_taxonomy,
    to_timeseries_dataframe,
)


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


def test_timeseries_utilities_are_public() -> None:
    assert callable(add_metadata_mapping)
    assert callable(mapping_to_taxonomy)
    assert callable(to_timeseries_dataframe)


def test_add_metadata_mapping_adds_multiple_attributes() -> None:
    source = pd.DataFrame(
        {
            "selskap": ["001", "001", "002"],
            "selskapsnavn": ["Company A", "Company A", "Company B"],
            "region": ["North", "North", "South"],
        }
    )
    dataset = _metadata_dataset()

    add_metadata_mapping(
        source,
        from_col="selskap",
        to_cols=["selskapsnavn", "region"],
        target_dataset=dataset,
    )

    company_a_tags = cast(dict[str, str], dataset.series_tags["001.rente"])
    company_b_tags = cast(dict[str, str], dataset.series_tags["002.rente"])
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


@pytest.mark.parametrize(
    "missing_parent",
    [None, pd.NA, float("nan"), "", "   "],
    ids=["none", "pd-na", "nan", "empty", "whitespace"],
)
def test_mapping_to_taxonomy_treats_missing_parent_as_root(
    missing_parent: Any,
) -> None:
    source = pd.DataFrame(
        {
            "child": ["A", "A1"],
            "parent": [missing_parent, "A"],
        }
    )

    taxonomy = mapping_to_taxonomy(source, "child", "parent")

    assert taxonomy.root == "A"
    assert taxonomy.root_nodes == ["A"]
    assert list(taxonomy.structure.edges) == [("A1", "A")]


def test_mapping_to_taxonomy_converts_codes_to_strings() -> None:
    source = pd.DataFrame(
        {
            "child": [1, 2],
            "parent": [None, 1],
        }
    )

    taxonomy = mapping_to_taxonomy(source, "child", "parent")

    assert taxonomy.root == "1"
    assert list(taxonomy.structure.edges) == [("2", "1")]
    assert taxonomy.entities.select(["code", "name", "parentCode"]).to_pylist() == [
        {"code": "1", "name": "1", "parentCode": None},
        {"code": "2", "name": "2", "parentCode": "1"},
    ]


def test_mapping_to_taxonomy_removes_duplicates_after_normalization() -> None:
    source = pd.DataFrame(
        {
            "child": [1, "1", 2],
            "parent": [None, "", 1],
        }
    )

    taxonomy = mapping_to_taxonomy(source, "child", "parent")

    assert taxonomy.entities.num_rows == 2


@pytest.mark.parametrize("missing_child", [None, pd.NA, float("nan")])
def test_mapping_to_taxonomy_rejects_missing_child(missing_child: Any) -> None:
    source = pd.DataFrame(
        {
            "child": [missing_child],
            "parent": [None],
        }
    )

    with pytest.raises(ValueError, match="child codes must not be missing"):
        mapping_to_taxonomy(source, "child", "parent")
