import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import requests

# ---- Load and clean dataset ----
costar_df = pd.read_csv("Costar_GEO_CLEANED_CA.csv")
costar_df["Zip"] = costar_df["Zip"].astype(str).str.strip().str[:5]
costar_df["City"] = costar_df["City"].astype(str).str.title().str.strip()

# ---- Sidebar Inputs ----
st.sidebar.header("📍 Filter Criteria")
cities = sorted(costar_df["City"].unique())
selected_city = st.sidebar.selectbox("City", cities)

zip_options = sorted(costar_df[costar_df["City"] == selected_city]["Zip"].unique())
selected_zip = st.sidebar.selectbox("ZIP Code", zip_options)

min_size = st.sidebar.slider("Min Space Size (SF)", 0, 1500000, 50000, step=10000)
min_parking = st.sidebar.slider("Min Parking Spaces", 0, 1000, 50, step=50)

# ---- Filter DataFrame ----
df = costar_df[
    (costar_df["City"] == selected_city) &
    (costar_df["Zip"] == selected_zip) &
    (costar_df["Total Available Space (SF)"] >= min_size) &
    (costar_df["Number Of Parking Spaces"] >= min_parking)
]

# ---- Display Summary ----
st.subheader("🔍 Predictive Analysis Summary")
st.markdown(f"""
- **ZIP Code**: `{selected_zip}`  
- **Average Rent**: ${df["Rent"].mean():.2f} / SF  
- **Average Size**: {df["Total Available Space (SF)"].mean():,.0f} SF  
- **Sites Found**: {len(df)}
""")

# ---- Build Map ----
m = folium.Map(location=[36.7783, -119.4179], zoom_start=7, tiles="OpenStreetMap")

# California outline
ca_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
geojson = requests.get(ca_url).json()
ca_shape = [f for f in geojson["features"] if f["properties"]["name"] == "California"]
folium.GeoJson(
    {"type": "FeatureCollection", "features": ca_shape},
    style_function=lambda x: {"color": "black", "weight": 1.5, "fillOpacity": 0}
).add_to(m)

# Plot points
cluster = MarkerCluster().add_to(m)
for _, row in df.iterrows():
    popup = folium.Popup(f"""
        <b>{row.get('Property Name', 'Unnamed')}</b><br>
        Address: {row.get('Property Address', '')}<br>
        Rent: ${row['Rent']}<br>
        Size: {row['Total Available Space (SF)']} SF<br>
        Parking: {row['Number Of Parking Spaces']}
    """, max_width=300)

    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=popup,
        icon=folium.Icon(color="darkblue", icon="building", prefix="fa", icon_color="yellow")
    ).add_to(cluster)

# ---- Show map using Streamlit Folium ----
st_data = st_folium(m, width=900, height=600)
