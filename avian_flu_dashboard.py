import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO

df = pd.read_csv("cleaned_bird_flu.csv")
pred = pd.read_csv("prediction_vs_actual.csv")

df_results = df.iloc[pred.index].copy()
df_results["Actual"] = pred["Actual"].values
df_results["Predicted"] = pred["Predicted"].values
df_results["Date"] = pd.to_datetime(df_results["Date"])

st.set_page_config(page_title="Avian Flu Dashboard", layout="wide")

st.title("🦠 Avian Influenza Outbreak Dashboard")
st.markdown("""
This dashboard helps monitor and analyze potential H5 HPAI outbreaks.
Use the sidebar filters to explore predictions by region, species, and time.
""")

st.sidebar.header("Filter Options")
county = st.sidebar.multiselect("Select County", df_results["County"].unique())
month = st.sidebar.multiselect("Select Month", sorted(df_results["Month"].unique()))
species = st.sidebar.multiselect("Select Parent Species", df_results["Parent_Species"].unique())

filtered = df_results.copy()
if county:
    filtered = filtered[filtered["County"].isin(county)]
if month:
    filtered = filtered[filtered["Month"].isin(month)]
if species:
    filtered = filtered[filtered["Parent_Species"].isin(species)]

st.subheader("📍 Predicted Outbreak Hotspots")
map_center = [filtered["Latitude"].mean(), filtered["Longitude"].mean()] if not filtered.empty else [0, 0]
m = folium.Map(location=map_center, zoom_start=4)
marker_cluster = MarkerCluster().add_to(m)

for _, row in filtered[filtered["Predicted"] == 1].iterrows():
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=5,
        color='red',
        fill=True,
        fill_opacity=0.7,
        popup=f"{row['County']} - {row['Parent_Species']}"
    ).add_to(marker_cluster)

st_data = st_folium(m, width=700, height=500)

st.subheader("📈 Actual vs Predicted Trend Over Time")
fig, ax = plt.subplots(figsize=(10, 4))
filtered_sorted = filtered.sort_values(by="Date")
sns.lineplot(data=filtered_sorted, x="Date", y="Actual", label="Actual", ax=ax)
sns.lineplot(data=filtered_sorted, x="Date", y="Predicted", label="Predicted", ax=ax)
ax.set_title("Outbreak Trend")
ax.set_ylabel("Outbreak (0 = No, 1 = Yes)")
ax.set_xlabel("Date")
st.pyplot(fig)

st.subheader("📋 High-Risk Summary Table")
summary = (
    filtered[filtered["Predicted"] == 1]
    .groupby(["County", "Month", "Parent_Species"])
    .size()
    .reset_index(name="Predicted_Outbreaks")
    .sort_values(by="Predicted_Outbreaks", ascending=False)
)

st.dataframe(summary)

st.subheader("🧠 Policy Recommendations")
policy_text = f"""
Recommendations:
1. Strengthen surveillance in these counties: {', '.join(summary['County'].unique()) or 'N/A'}
2. Focus monitoring during these months: {', '.join(summary['Month'].astype(str).unique()) or 'N/A'}
3. Prioritize monitoring of these bird species: {', '.join(summary['Parent_Species'].unique()) or 'N/A'}
4. Implement early warning systems and local alert mechanisms.
"""
st.text_area("Generated Recommendation:", policy_text, height=180)

st.subheader("📦 Download Reports")
csv_buf = StringIO()
summary.to_csv(csv_buf, index=False)
st.download_button("Download High-Risk Summary (CSV)", csv_buf.getvalue(), file_name="high_risk_summary.csv")

txt_buf = StringIO()
txt_buf.write(policy_text)
st.download_button("Download Recommendation (TXT)", txt_buf.getvalue(), file_name="policy_recommendation.txt")
