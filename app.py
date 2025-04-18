import streamlit as st
import pandas as pd
from pathlib import Path

# Determine base directory (where this script resides)
BASE_DIR = Path(__file__).resolve().parent

# Configuration: file paths
CODES_FILE = BASE_DIR / "codes.xlsx"
VOTES_FILE = BASE_DIR / "votes.csv"
ADMIN_CODE = "ADMIN123"  # Change this to your admin code

# Define your voting categories and corresponding candidate files
CANDIDATE_FILES = {
    "CategoryA": BASE_DIR / "categoryA.xlsx",
    "CategoryB": BASE_DIR / "categoryB.xlsx",
}

st.title("Simple Voting Service")

@st.cache_data
def load_codes():
    try:
        df = pd.read_excel(CODES_FILE, dtype=str, header=None)
        return df.iloc[:, 0].str.strip().tolist()
    except Exception as e:
        st.error(f"Could not load codes from {CODES_FILE.name}: {e}")
        return []

@st.cache_data
def load_candidates(file_path):
    try:
        df = pd.read_excel(file_path, dtype=str)
        # Expect first row as headers (subcategories) and candidates below
        df = df.dropna(axis=1, how="all")  # remove empty columns
        return df
    except Exception as e:
        st.error(f"Could not load candidates from {file_path.name}: {e}")
        return pd.DataFrame()

codes = load_codes()

# Login screen
code = st.text_input("Enter your 5-character code:")
if not code:
    st.stop()
code = code.strip()

if code == ADMIN_CODE:
    # Admin view
    st.header("Admin Dashboard")
    if VOTES_FILE.exists():
        votes_df = pd.read_csv(VOTES_FILE, dtype=str)
        results = []
        for category, path in CANDIDATE_FILES.items():
            if category in votes_df.columns:
                counts = votes_df[category].value_counts()
                if not counts.empty:
                    top = counts.idxmax()
                    cnt = counts.max()
                    results.append({"Category": category, "Top Candidate": top, "Votes": cnt})
        if results:
            res_df = pd.DataFrame(results)
            st.table(res_df)
            with open(VOTES_FILE, "rb") as f:
                st.download_button("Download raw votes", f, file_name=VOTES_FILE.name, mime="text/csv")
        else:
            st.info("No votes recorded yet.")
    else:
        st.info("No votes recorded yet.")

elif code in codes:
    # Voter view
    st.success("Welcome! Please cast your votes below.")
    vote_data = {"code": code}
    for category, file_path in CANDIDATE_FILES.items():
        st.subheader(category)
        if not file_path.exists():
            st.warning(f"Candidate file for {category} not found: {file_path.name}")
            continue
        df = load_candidates(file_path)
        if df.empty:
            continue
        subcategories = df.columns.tolist()
        chosen_sub = st.selectbox(f"Choose subcategory for {category}", subcategories, key=f"sub_{category}")
        options = df[chosen_sub].dropna().tolist()
        if not options:
            st.warning(f"No candidates listed under {chosen_sub}.")
            continue
        choice = st.radio(f"Select candidate for {category}", options, key=f"cand_{category}")
        vote_data[category] = choice
    if st.button("Submit Vote"):
        new_vote = pd.DataFrame([vote_data])
        try:
            if VOTES_FILE.exists():
                new_vote.to_csv(VOTES_FILE, mode="a", header=False, index=False)
            else:
                new_vote.to_csv(VOTES_FILE, index=False)
            st.success("Your vote has been recorded. Thank you!")
        except Exception as e:
            st.error(f"Error saving vote: {e}")
        st.stop()
else:
    st.error("Invalid code. Please try again.")
