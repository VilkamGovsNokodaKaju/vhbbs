import streamlit as st
import pandas as pd
from pathlib import Path

# Configuration
ADMIN_CODE = "ADMIN123"  # Change to your actual admin code
VOTE_FILE = "votes.csv"

# Candidate category mapping: category -> (xlsx_filename, csv_filename)
CANDIDATE_FILES = {
    "candidates": ("candidates.xlsx", "candidates.csv"),
    "candidates": ("candidates.xlsx", "candidates.csv"),
}

st.title("Simple Voting Service")

@st.cache_data
def find_file(name: str) -> Path | None:
    """Locate a file in the working directory, case-insensitive."""
    p = Path(name)
    if p.exists():
        return p
    for f in Path().iterdir():
        if f.name.lower() == name.lower():
            return f
    return None

@st.cache_data
def load_codes():
    """Load list of valid voter codes from CSV or XLSX."""
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
    st.error("No codes file found (codes.csv or codes.xlsx).")
    return []

@st.cache_data
def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
    """Load candidate matrix for a category from CSV or XLSX."""
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
        for cat, (xlsx, csv) in CANDIDATE_FILES.items():
            st.subheader(f"Top 10 for {cat}")
            if cat in votes_df.columns:
                counts = votes_df[cat].value_counts().head(10)
                if not counts.empty:
                    df_top = counts.reset_index()
                    df_top.columns = ["Candidate", "Votes"]
                    st.table(df_top)
                else:
                    st.info("No votes cast in this category yet.")
            else:
                st.info("No votes cast in this category yet.")
        with open(votes_path, "rb") as f:
            st.download_button("Download full votes", f, file_name=votes_path.name)
    else:
        st.info("No votes recorded yet.")

# Voter view
elif code in codes:
    # Prevent double voting
    votes_path = find_file(VOTE_FILE)
    if votes_path and votes_path.exists():
        try:
            existing = pd.read_csv(votes_path, dtype=str)
            if code in existing.get('code', []).tolist():
                st.warning("Our records show you've already voted. Thank you!")
                st.stop()
        except Exception as e:
            st.error(f"Error checking previous votes: {e}")
            st.stop()

    st.success("Welcome! Please cast your vote for each category.")
    vote = {"code": code}
    errors = []
    for cat, (xlsx, csv) in CANDIDATE_FILES.items():
        st.subheader(cat)
        df = load_candidates(xlsx, csv)
        if df.empty:
            st.warning(f"No candidate data for {cat}.")
            continue
        subs = df.columns.tolist()
        choice_sub = st.selectbox(f"Select subcategory for {cat}", ["-- Select --"] + subs, key=f"sub_{cat}")
        if choice_sub == "-- Select --":
            errors.append(f"Subcategory for {cat} not selected.")
            continue
        opts = df[choice_sub].dropna().tolist()
        choice_cand = st.selectbox(f"Select candidate for {cat}", ["-- Select --"] + opts, key=f"cand_{cat}")
        if choice_cand == "-- Select --":
            errors.append(f"Candidate for {cat} not selected.")
        else:
            vote[cat] = choice_cand
    if st.button("Submit Vote"):
        if errors:
            st.error("\n".join(errors))
        else:
            try:
                new_df = pd.DataFrame([vote])
                votes_path = votes_path or Path(VOTE_FILE)
                new_df.to_csv(votes_path, mode="a" if votes_path.exists() else "w", header=not votes_path.exists(), index=False)
                st.success("Your vote has been recorded. Thank you!")
            except Exception as e:
                st.error(f"Error saving vote: {e}")
        st.stop()

else:
    st.error("Invalid code.")
