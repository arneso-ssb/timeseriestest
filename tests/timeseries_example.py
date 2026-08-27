from pathlib import Path

import pandas as pd
from ssb_timeseries.dataset import Dataset
from ssb_timeseries.types import SeriesType

data = pd.read_csv(Path("kpi.csv"), parse_dates=["valid_at"])

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

print(cpi.pd)
print(cpi.series)

# Vis utviklingen for noen utvalgte grupper.
selected = cpi.select(
    "00 I alt",
    "01 Matvarer og alkoholfrie drikkevarer",
    "04 Bolig, elektrisitet og brensel",
)

print(selected.pd)

# Differanse i indekspoeng fra referanseverdien 100.
difference_from_reference = selected - 100
print(difference_from_reference.pd)

# Glatt utviklingen med et tremåneders glidende gjennomsnitt.
moving_average = selected.moving_average(start=-2, stop=0)
print(moving_average.pd)
