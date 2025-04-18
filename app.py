import streamlit as st
import pandas as pd
from pathlib import Path

# Configuration: file names in the repo root
CODES_CSV = Path("codes.csv")
CODES_XLSX = Path("codes.xlsx")
VOTES_FILE = Path("votes.csv")
ADMIN_CODE = "ADMIN123"  # Change to your actual admin code

# Each entry: (xlsx_filename, csv_filename)
CANDIDATE_FILES = {
    "CategoryA": ("categoryA.xlsx", "categoryA.csv"),
    "CategoryB": ("categoryB.xlsx", "categoryB.csv"),
}

st.title("Simple Voting Service")

@st.cache_data
def load_codes():
    # Try CSV first (no openpyxl needed), then XLSX
    if CODES_CSV.exists():
        try:
            df = pd.read_csv(CODES_CSV, header=None, dtype=str)
            return df.iloc[:, 0].str.strip().tolist()
        except Exception as e:
            st.error(f"Could not load codes from {CODES_CSV.name}: {e}")
            return []
    if CODES_XLSX.exists():
        try:
            df = pd.read_excel(CODES_XLSX, header=None, dtype=str)
            return df.iloc[:, 0].str.strip().tolist()
        except Exception as e:
            st.error(f"Could not load codes from {CODES_XLSX.name}: {e}")
            return []
    st.error("No codes file found (codes.csv or codes.xlsx).")
    return []

@st.cache_data
def load_candidates(xlsx_file=None, csv_file=None):
    # CSV fallback for simpler dependency
    if csv_file and Path(csv_file).exists():
        try:
            df = pd.read_csv(csv_file, dtype=str)
            return df.dropna(axis=1, how="all")
        except Exception as e:
            st.error(f"Could not load candidates from {csv_file}: {e}")
            return pd.DataFrame()
    if xlsx_file and Path(xlsx_file).exists():
        try:
            df = pd.read_excel(xlsx_file, dtype=str)
            return df.dropna(axis=1, how="all")
        except Exception as e:
            st.error(f"Could not load candidates from {xlsx_file}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

codes = load_codes()

# Login
code = st.text_input("Enter your 5-character code:")
if not code:
    st.stop()
code = code.strip()

if code == ADMIN_CODE:
    st.header("Admin Dashboard")
    if VOTES_FILE.exists():
        votes_df = pd.read_csv(VOTES_FILE, dtype=str)
        results = []
        for category, (xlsx, csv_) in CANDIDATE_FILES.items():
            if category in votes_df.columns:
                counts = votes_df[category].value_counts()
                if not counts.empty:
                    top, cnt = counts.idxmax(), counts.max()
                    results.append({"Category": category, "Top": top, "Votes": cnt})
        if results:
            st.table(pd.DataFrame(results))
            with open(VOTES_FILE, "rb") as f:
                st.download_button("Download votes", f, file_name=VOTES_FILE.name)
        else:
            st.info("No votes recorded yet.")
    else:
        st.info("No votes recorded yet.")

elif code in codes:
    st.success("Welcome! Cast your votes below.")
    vote = {"code": code}
    for category, (xlsx, csv_) in CANDIDATE_FILES.items():
        st.subheader(category)
        df = load_candidates(xlsx, csv_)
        if df.empty:
            st.warning(f"No candidate data for {category}.")
            continue
        subs = df.columns.tolist()
        choice_sub = st.selectbox(f"Subcategory for {category}", subs, key=f"sub_{category}")
        opts = df[choice_sub].dropna().tolist()
        if not opts:
            st.warning(f"No candidates under {choice_sub}.")
            continue
        vote_choice = st.radio(f"Choose for {category}", opts, key=f"rad_{category}")
        vote[category] = vote_choice
    if st.button("Submit Vote"):
        new = pd.DataFrame([vote])
        try:
            new.to_csv(VOTES_FILE, mode="a" if VOTES_FILE.exists() else "w", header=not VOTES_FILE.exists(), index=False)
            st.success("Vote recorded. Thank you!")
        except Exception as e:
            st.error(f"Error saving vote: {e}")
        st.stop()
else:
    st.error("Invalid code.")
