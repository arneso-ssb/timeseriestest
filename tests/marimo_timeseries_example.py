import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import pandas as pd
    from ssb_timeseries.dataset import Dataset
    from ssb_timeseries.types import SeriesType

    return Dataset, Path, SeriesType, pd


@app.cell
def _(Path, pd):
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
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
