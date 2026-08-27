import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Example of using ssb-timeseries
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import pandas as pd
    from ssb_timeseries.dataset import Dataset
    from ssb_timeseries.types import SeriesType

    return Dataset, Path, SeriesType, pd


@app.cell
def _(Path, pd):
    # Read consumer price index from csv-file
    data = pd.read_csv(Path("kpi.csv"), parse_dates=["valid_at"])
    data
    return (data,)


@app.cell
def _(Dataset, SeriesType, data):
    cpi = Dataset(
        name="konsumprisindeks_etter_vare_og_tjenestegruppe",
        data_type=SeriesType.simple(),
        data=data,
        find_existing=False,
    )

    cpi.tag_dataset(
        statistikk="Konsumprisindeksen",
        kilde="Statistisk sentralbyrå",
        statistikkbanktabell="14700",
        frekvens="månedlig",
        enhet="indeks",
        referanseår="2025=100",
    )
    cpi.series
    return (cpi,)


@app.cell
def _(cpi):
    # Show the developement for a selected subset of series
    selected = cpi.select(
        "00 I alt",
        "01 Matvarer og alkoholfrie drikkevarer",
        "04 Bolig, elektrisitet og brensel",
    )
    selected.pd
    return (selected,)


@app.cell
def _(selected):
    # Calculate deiffrence from reference for all series
    difference_from_reference = selected - 100
    difference_from_reference.pd
    return


@app.cell
def _(selected):
    # Calculate moving average
    moving_average = selected.moving_average(start=-2, stop=0)
    moving_average.pd
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
