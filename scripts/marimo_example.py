import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd

    return (pd,)


@app.cell
def _(pd):
    dataframe = pd.DataFrame(
        {
            "city": ["Oslo", "Bergen", "Trondheim"],
            "temperature_c": [12.4, 11.8, 10.2],
        }
    )
    dataframe
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
