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

    import altair as alt
    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd
    from ssb_timeseries.dataset import Dataset
    from ssb_timeseries.types import SeriesType

    return Dataset, Path, SeriesType, alt, mo, pd, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Read dataset
    """)
    return


@app.cell
def _(Path, pd):
    # Read consumer price index from csv-file
    data = pd.read_csv(Path("kpi.csv"), parse_dates=["valid_at"])
    data
    return (data,)


@app.cell
def _(pd):
    def round_floats(df: pd.DataFrame, decimals: int = 1) -> pd.DataFrame:
        """Return a dataframe with float values formatted to the specified number of decimals."""
        float_columns = df.select_dtypes(include="float").columns

        return df.round({column: decimals for column in float_columns})

    return (round_floats,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Create timeseries dataset
    """)
    return


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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Calculations
    """)
    return


@app.cell
def _(round_floats, selected):
    # Calculate deiffrence from reference for all series
    difference_from_reference = selected - 100
    round_floats(difference_from_reference.pd)
    return


@app.cell
def _(round_floats, selected):
    # Calculate moving average
    moving_average = selected.moving_average(start=-2, stop=0)
    round_floats(moving_average.pd)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plotting
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Built-in
    """)
    return


@app.cell
def _(plt, selected):
    ax = selected.plot(marker="o")

    ax.set_title("Konsumprisindeksen etter vare- og tjenestegruppe")
    ax.set_xlabel("")
    ax.set_ylabel("Indeks (2025 = 100)")
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Using Altair
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Select which groups you want to plot:
    """)
    return


@app.cell
def _(cpi, mo):
    series_picker = mo.ui.multiselect(
        options=cpi.series,
        value=[
            "00 I alt",
            "01 Matvarer og alkoholfrie drikkevarer",
            "04 Bolig, elektrisitet og brensel",
        ],
        label="Vare- og tjenestegrupper",
        max_selections=5,
    )

    series_picker
    return (series_picker,)


@app.cell
def _(cpi, series_picker):
    # Make the data suitable for plotting with Altair
    plot_data = cpi.pd.melt(
        id_vars="valid_at",
        value_vars=series_picker.value,
        var_name="varegruppe",
        value_name="indeks",
    )
    return (plot_data,)


@app.cell
def _(alt, plot_data):
    cpi_chart = (
        alt.Chart(plot_data)
        .mark_line(
            point=True,
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "valid_at:T",
                title=None,
                axis=alt.Axis(
                    format="%b %Y",
                    labelAngle=-45,
                    grid=False,
                ),
            ),
            y=alt.Y(
                "indeks:Q",
                title="Indeks (2025 = 100)",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "varegruppe:N",
                title=None,
                legend=alt.Legend(
                    orient="bottom",
                    columns=1,
                    labelLimit=600,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "valid_at:T",
                    title="Måned",
                    format="%Y-%m",
                ),
                alt.Tooltip(
                    "varegruppe:N",
                    title="Vare- og tjenestegruppe",
                ),
                alt.Tooltip(
                    "indeks:Q",
                    title="KPI",
                    format=".1f",
                ),
            ],
        )
        .properties(
            title="Konsumprisindeksen etter vare- og tjenestegruppe",
            width="container",
            height=420,
        )
        .configure_axis(
            gridColor="#e5e7eb",
            gridOpacity=0.1,
            labelFontSize=12,
            titleFontSize=13,
        )
        .configure_view(strokeWidth=0)
    )

    cpi_chart
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Changes from last period and last year
    """)
    return


@app.cell
def _(cpi, round_floats):
    monthly_percentage_change = (
        cpi.pd.set_index(
            "valid_at"
        )  # Removes the date column from the change calculation
        .pct_change()
        .mul(100)
    )
    round_floats(monthly_percentage_change.tail(1))
    return


@app.cell
def _(cpi, round_floats):
    yearly_percentage_change = (
        cpi.pd.set_index("valid_at").pct_change(periods=12).mul(100)
    )
    round_floats(yearly_percentage_change.tail(1))
    return


if __name__ == "__main__":
    app.run()
