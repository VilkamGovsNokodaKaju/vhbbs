import streamlit as st
import pandas as pd
from pathlib import Path

# Configuration
ADMIN_CODE = "ADMIN123"  # Change to your actual admin code
VOTE_FILE = "votes.csv"

# Candidate category mapping: category -> (xlsx_filename, csv_filename)
CANDIDATE_FILES = {
    "CategoryA": ("candidates.xlsx", "candidates.csv"),
    "CategoryB": ("candidates", "candidates.csv"),
}

st.title("Simple Voting Service")

# Helper to find a file by name, case-insensitive
@st.cache_data

def find_file(name: str) -> Path | None:
    p = Path(name)
    if p.exists():
        return p
    for f in Path().iterdir():
        if f.name.lower() == name.lower():
            return f
    return None

@st.cache_data
def load_codes():
    # Try CSV first, then XLSX
    for name in ("codes.csv", "codes.xlsx"):
        path = find_file(name)
        if path:
            try:
                if path.suffix.lower() == ".csv":
                    df = pd.read_csv(path, header=None, dtype=str)
                else:
                    df = pd.read_excel(path, header=None, dtype=str)
                return df.iloc[:, 0].str.strip().tolist()
            except Exception as e:
                st.error(f"Error loading codes from {path.name}: {e}")
                return []
    st.error("No codes file found (codes.csv or codes.xlsx) in app directory.")
    return []

@st.cache_data
def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
    # CSV fallback
    path_csv = find_file(csv_name)
    if path_csv:
        try:
            return pd.read_csv(path_csv, dtype=str).dropna(axis=1, how="all")
        except Exception as e:
            st.error(f"Error loading {path_csv.name}: {e}")
            return pd.DataFrame()
    path_xlsx = find_file(xlsx_name)
    if path_xlsx:
        try:
            return pd.read_excel(path_xlsx, dtype=str).dropna(axis=1, how="all")
        except Exception as e:
            st.error(f"Error loading {path_xlsx.name}: {e}")
            return pd.DataFrame()
    st.error(f"No candidate file found for {xlsx_name} or {csv_name}.")
    return pd.DataFrame()

codes = load_codes()

# Login screen
code = st.text_input("Enter your 5-character code:")
if not code:
    st.stop()
code = code.strip()

# Admin view
if code == ADMIN_CODE:
    st.header("Admin Dashboard")
    votes_path = find_file(VOTE_FILE)
    if votes_path and votes_path.exists():
        votes_df = pd.read_csv(votes_path, dtype=str)
        results = []
        for cat, (xlsx, csv) in CANDIDATE_FILES.items():
            if cat in votes_df.columns:
                counts = votes_df[cat].value_counts()
                if not counts.empty:
                    top, cnt = counts.idxmax(), counts.max()
                    results.append({"Category": cat, "Top": top, "Votes": cnt})
        if results:
            st.table(pd.DataFrame(results))
            with open(votes_path, "rb") as f:
                st.download_button("Download votes", f, file_name=votes_path.name)
        else:
            st.info("No votes recorded yet.")
    else:
        st.info("No votes recorded yet.")

# Voter view
elif code in codes:
    st.success("Welcome! Cast your votes below.")
    vote = {"code": code}
    for cat, (xlsx, csv) in CANDIDATE_FILES.items():
        st.subheader(cat)
        df = load_candidates(xlsx, csv)
        if df.empty:
            st.warning(f"No candidate data for {cat}.")
            continue
        subs = df.columns.tolist()
        choice_sub = st.selectbox(f"Subcategory for {cat}", subs, key=f"sub_{cat}")
        opts = df[choice_sub].dropna().tolist()
        if not opts:
            st.warning(f"No candidates under {choice_sub}.")
            continue
        vote_choice = st.radio(f"Choose for {cat}", opts, key=f"rad_{cat}")
        vote[cat] = vote_choice
    if st.button("Submit Vote"):
        new_df = pd.DataFrame([vote])
        votes_path = find_file(VOTE_FILE) or Path(VOTE_FILE)
        try:
            new_df.to_csv(votes_path, mode="a" if votes_path.exists() else "w", header=not votes_path.exists(), index=False)
            st.success("Your vote has been recorded. Thank you!")
        except Exception as e:
            st.error(f"Error saving vote: {e}")
        st.stop()

else:
    st.error("Invalid code.")
