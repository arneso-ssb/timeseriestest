"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """TimeseriesTest."""


if __name__ == "__main__":
    main(prog_name="timeseriestest")  # pragma: no cover
