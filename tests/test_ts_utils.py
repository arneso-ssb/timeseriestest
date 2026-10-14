from typing import cast

import pandas as pd
import pytest
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType

from timeseriestest.ts_utils import add_metadata_mapping


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
