from email.policy import default
from pathlib import Path
import math

import geopandas
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    layout="wide", page_title="Exploration des loyers encadrés à Lyon", page_icon="📈"
)

DATA_PATH = Path("data/data_clean.json")

NON_NUMERIC_COLUMNS = ["codeiris", "zonage", "commune", "insee", "gid", "geometry"]


@st.cache
def get_data(file_path: Path) -> geopandas.GeoDataFrame:

    gdf = geopandas.read_file(file_path)
    gdf = pd.concat((gdf, pd.json_normalize(gdf.valeurs.values.tolist())), axis=1)

    melted_gdf = gdf.melt(
        id_vars=gdf.columns[~gdf.columns.str.contains(r"1\.|2\.|3\.|4 et plus\.")],
        value_vars=gdf.columns[gdf.columns.str.contains(r"1\.|2\.|3\.|4 et plus\.")],
    )

    clean_gdf = melted_gdf.drop(columns="variable").join(
        pd.DataFrame(
            melted_gdf.variable.str.split(".").tolist(),
            columns=["number_of_rooms", "construction_year", "flat_type", "variable"],
            index=melted_gdf.index,
        )
    )

    final_gdf = pd.merge(
        gdf[["codeiris", "zonage", "commune", "insee", "gid", "geometry"]],
        clean_gdf.pivot_table(
            index=["codeiris", "number_of_rooms", "construction_year", "flat_type"],
            columns="variable",
            values="value",
        ).reset_index(),
        left_on="codeiris",
        right_on="codeiris",
        how="right",
        validate="one_to_many",
    ).reset_index()

    return final_gdf


gdf = get_data(DATA_PATH)

st.title("Visualisation des loyers de référence à Lyon 🔍")

num_rooms_filters = {
    "1 pièce": "1",
    "2 pièces": "2",
    "3 pièces": "3",
    "4 pièces et plus": "4 et plus",
}

construction_year_filters = {
    "Avant 1946": "avant 1946",
    "Entre 1946 et 1970": "1946-70",
    "Entre 1971 et 1990": "1971-90",
    "Après 1990": "après 1990",
}


flat_type_filters = {
    "Meublé": "meuble",
    "Non meublé": "non meuble",
}
col1, col2, col3 = st.columns(3)

with col1:
    num_rooms = st.multiselect(
        "Taille du logement",
        options=num_rooms_filters.keys(),
        default=num_rooms_filters.keys(),
    )

with col2:
    construction_year = st.multiselect(
        "Année de construction",
        options=construction_year_filters.keys(),
        default="Après 1990",
    )

with col3:
    flat_type = st.multiselect(
        "Type de logement", options=flat_type_filters.keys(), default="Non meublé"
    )

num_rooms_df_filter = [num_rooms_filters[e] for e in num_rooms]
construction_year_df_filter = [construction_year_filters[e] for e in construction_year]
flat_type_df_filter = [flat_type_filters[e] for e in flat_type]

selected_gdf_mean = (
    gdf.loc[
        (gdf.construction_year.isin(construction_year_df_filter))
        & (gdf.flat_type.isin(flat_type_df_filter))
        & (gdf.number_of_rooms.isin(num_rooms_df_filter)),
    ]
    .groupby("codeiris")
    .agg(value=("loyer_reference_majore", "mean"), geometry=("geometry", "first"))
)
selected_gdf_mean = geopandas.GeoDataFrame(selected_gdf_mean)

fig = px.choropleth_mapbox(
    selected_gdf_mean,
    geojson=selected_gdf_mean.geometry,
    locations=selected_gdf_mean.index,
    color=selected_gdf_mean.value.round(2),
    center={"lat": 45.764043, "lon": 4.835659},
    mapbox_style="open-street-map",
    zoom=11,
    height=600,
    width=900,
    opacity=0.5,
    labels={"color": "Loyer de référence majoré moyen (€/m²)"},
    color_continuous_scale=["#fee6ce", "#fdae6b", "#e6550d"],
    range_color=[
        math.floor(selected_gdf_mean.value.min()),
        math.ceil(selected_gdf_mean.value.max()),
    ],
)

st.plotly_chart(fig, use_container_width=True)
