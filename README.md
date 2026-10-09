# TimeseriesTest

[![PyPI](https://img.shields.io/pypi/v/timeseriestest.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/timeseriestest.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/timeseriestest)][pypi status]
[![License](https://img.shields.io/pypi/l/timeseriestest)][license]

[![Tests](https://github.com/arneso-ssb/timeseriestest/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=arneso-ssb_timeseriestest&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=arneso-ssb_timeseriestest&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

[pypi status]: https://pypi.org/project/timeseriestest/
[tests]: https://github.com/arneso-ssb/timeseriestest/actions?workflow=Tests
[sonarcov]: https://sonarcloud.io/summary/overall?id=arneso-ssb_timeseriestest
[sonarquality]: https://sonarcloud.io/summary/overall?id=arneso-ssb_timeseriestest
[pre-commit]: https://github.com/pre-commit/pre-commit

## Features

- Transfer Parquet data through portable CSV and JSON text files.
- Preserve Arrow datatypes, nullability, field metadata, and schema metadata.

## Requirements

- TODO

## Installation

You can install _TimeseriesTest_ via [pip] or [uv] from [PyPI]:

```console
uv add timeseriestest
```

## Usage

Export a Parquet file into a transfer directory:

```python
from pathlib import Path

from timeseriestest import parquet_to_text

parquet_to_text(Path("input/measurements.parquet"), Path("transfer"))
```

This creates `transfer/data.csv` and `transfer/metadata.json`. The JSON file
contains a readable schema and the exact serialized Arrow schema used for
reconstruction.

Recreate the Parquet file in another directory:

```python
from pathlib import Path

from timeseriestest import text_to_parquet

text_to_parquet(Path("transfer"), Path("output"))
```

The original filename is restored. Scalar Arrow types, including numeric,
decimal, temporal, binary, string, and dictionary/categorical types, are
preserved. Nested types such as lists and structs are not supported by the CSV
intermediate format. Parquet-specific physical details such as compression,
encoding, and row-group layout are recreated with PyArrow defaults.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_TimeseriesTest_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from a template adapted from Statistics Norway's [SSB PyPI Template].

[pypi]: https://pypi.org/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/arneso-ssb/timeseriestest/issues
[uv]: https://github.com/astral-sh/uv

<!-- github-only -->

[license]: https://github.com/arneso-ssb/timeseriestest/blob/main/LICENSE
[contributor guide]: https://github.com/arneso-ssb/timeseriestest/blob/main/CONTRIBUTING.md
