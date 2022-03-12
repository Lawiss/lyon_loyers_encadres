from email.policy import default
from pathlib import Path

import geopandas
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path("data/car_care.carencadrmtloyer_latest.json")

NON_NUMERIC_COLUMNS = ["codeiris", "zonage", "commune", "insee", "gid", "geometry"]


@st.cache
def get_data(file_path: Path) -> geopandas.GeoDataFrame:

    gdf = geopandas.read_file(file_path)
    gdf = pd.concat((gdf, pd.json_normalize(gdf.valeurs.values.tolist())), axis=1)

    return gdf


gdf = get_data(DATA_PATH)

st.title("Visualisation des loyers de référence à Lyon")

num_rooms_filters = {
    "1 pièce": "1.+\.loyer_reference_majore$",
    "2 pièces": "2.+\.loyer_reference_majore$",
    "3 pièces": "3.+\.loyer_reference_majore$",
    "4 pièces et plus": "4 et plus.+\.loyer_reference_majore$",
}

construction_year_filters = {
    "Avant 1946": ".+\.avant 1946.+\.loyer_reference_majore$",
    "Entre 1946 et 1970": ".+\.1946-70.+\.loyer_reference_majore$",
    "Entre 1971 et 1990": ".+\.1971-90.+\.loyer_reference_majore$",
    "Après 1990": ".+\.après 1990.+\.loyer_reference_majore$",
}


flat_type_filters = {
    "Meublé": ".+\.meuble\.loyer_reference_majore$",
    "Non meublé": ".+\.non meuble\.loyer_reference_majore$",
}

num_rooms = st.multiselect(
    "Taille du logement",
    options=num_rooms_filters.keys(),
    default=num_rooms_filters.keys(),
)

construction_year = st.multiselect(
    "Année de construction",
    options=construction_year_filters.keys(),
    default="Après 1990",
)

flat_type = st.multiselect("Type de logement", options=flat_type_filters.keys())

regex_num_rooms = "|".join([num_rooms_filters[e] for e in num_rooms])
regex_construction_year = "|".join(
    [construction_year_filters[e] for e in construction_year]
)
flat_type_regex = "|".join([flat_type_filters[e] for e in flat_type])

print(
    gdf.loc[
        :,
        gdf.columns.str.match(regex_num_rooms)
        & gdf.columns.str.match(regex_construction_year)
        & gdf.columns.str.match(flat_type_regex),
    ]
)

fig = px.choropleth_mapbox(
    gdf,
    geojson=gdf.geometry,
    locations=gdf.index,
    color=gdf.loc[
        :,
        gdf.columns.str.match(regex_num_rooms)
        & gdf.columns.str.match(regex_construction_year)
        & gdf.columns.str.match(flat_type_regex),
    ].mean(axis=1),
    center={"lat": 45.764043, "lon": 4.835659},
    mapbox_style="open-street-map",
    zoom=11,
    height=600,
    width=1000,
    opacity=0.4,
    labels={"color": "Loyer de référence majoré moyen (€/m²)"},
)

st.plotly_chart(fig)
