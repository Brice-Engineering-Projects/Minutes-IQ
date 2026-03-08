# src/minutes_iq/dashboard/dashboard.py

"""
Dashboard for Minutes IQ Keyword Matches
- Select any extracted CSV from dropdown
- Displays keyword match summary
- Filters results by keyword, date, and named entities
- Allows quick insight into what topics are surfacing in meetings
"""

import glob
import os
from pathlib import Path

import pandas as pd
import streamlit as st

# === Config ===
st.set_page_config(page_title="JEA Minutes Dashboard", layout="wide")
data_path = Path(__file__).resolve().parents[2] / "data" / "processed"

# === Helper: Get all extracted CSVs ===
csv_files = sorted(
    glob.glob(str(data_path / "extracted_mentions_*.csv")),
    key=os.path.getmtime,
    reverse=True,
)

if not csv_files:
    st.error("❌ No extracted_mentions_*.csv file found in processed data folder.")
    st.stop()

# === Sidebar: Select file ===
st.sidebar.header("📂 Data File Selection")
selected_csv = st.sidebar.selectbox(
    "Choose a data file to analyze:",
    options=[os.path.basename(f) for f in csv_files],
    format_func=lambda x: x.replace("extracted_mentions_", "").replace(".csv", ""),
)

csv_file = data_path / selected_csv

# === Load Data ===
df = pd.read_csv(csv_file)
df["file"] = df["file"].astype(str)
df["keyword"] = df["keyword"].astype(str)
df["snippet"] = df["snippet"].astype(str)
df["entities"] = df.get("entities", pd.Series([""] * len(df))).astype(str)
df["date"] = df["file"].str.extract(r"(20\d{2}[\-_]\d{2})")[0]


# === Entity Parsing ===
def extract_unique_entities(entities_series):
    flat_list = []
    for row in entities_series.dropna():
        flat_list.extend([e.strip() for e in row.split(",") if e.strip()])
    return sorted(set(flat_list))


unique_entities = extract_unique_entities(df["entities"])

# === Sidebar Filters ===
st.sidebar.header("🔍 Filters")
keyword_filter = st.sidebar.multiselect(
    "Keyword(s)", sorted(df["keyword"].unique()), default=df["keyword"].unique()
)
date_filter = st.sidebar.multiselect(
    "Date (YYYY-MM)",
    sorted(df["date"].dropna().unique()),
    default=df["date"].dropna().unique(),
)
entity_filter = st.sidebar.multiselect(
    "Named Entities (optional)", unique_entities, default=unique_entities
)


# === Filtered Data ===
def row_matches_entities(row):
    return any(ent in row["entities"] for ent in entity_filter)


filtered_df = df[
    df["keyword"].isin(keyword_filter)
    & df["date"].isin(date_filter)
    & df.apply(row_matches_entities, axis=1)
]

# === Main Panel ===
st.title("📊 JEA Meeting Minutes Intelligence Dashboard")
st.markdown(f"**Data file:** `{selected_csv}`")
st.metric("Matches Found", len(filtered_df))

st.markdown("---")
st.subheader("🔑 Keyword Frequency")
keyword_counts = filtered_df["keyword"].value_counts()
st.bar_chart(keyword_counts)

st.markdown("---")
st.subheader("📄 Matched Mentions")
st.dataframe(
    filtered_df[["file", "page", "keyword", "snippet", "entities"]],
    use_container_width=True,
)

st.caption("📁 Source file: " + selected_csv)
