import streamlit as st
import pandas as pd
from pathlib import Path

# Configuration
ADMIN_CODE = "ADMIN123"  # Change to your actual admin code
VOTE_FILE = "votes.csv"

# Candidate category mapping: category -> (xlsx_filename, csv_filename)
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

st.title("Simple Voting Service")

# Show thank-you screen if redirected here
params = st.query_params()
if "thanks" in params:
    st.header("Thank You!")
    st.write("Your vote has been successfully recorded.")
    st.stop()

# Helper to find a file by name, case-insensitive (uncached to detect new files)
def find_file(name: str) -> Path | None:
    p = Path(name)
    if p.exists():
        return p
    for f in Path().iterdir():
        if f.name.lower() == name.lower():
            return f
    return None

# Load list of valid voter codes
@st.cache_data
def load_codes() -> list:
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

# Load candidate options for a category
@st.cache_data
def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
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

# Load valid codes once
df_codes = load_codes()

# Prompt for voter/admin code
code = st.text_input("Enter your 5-character code:")
if not code:
    st.stop()
code = code.strip()

# Admin view
def show_admin():
    st.header("Admin Dashboard")
    votes_path = find_file(VOTE_FILE)
    # Display results
    if votes_path and votes_path.exists():
        votes_df = pd.read_csv(votes_path, dtype=str)
        cats = [col for col in votes_df.columns if col != 'code']
        if not cats:
            st.info("No votes recorded yet.")
        else:
            for cat in cats:
                st.subheader(f"Top 10 for {cat}")
                counts = votes_df[cat].value_counts().head(10)
                if not counts.empty:
                    df_top = counts.reset_index()
                    df_top.columns = ["Candidate", "Votes"]
                    st.table(df_top)
                else:
                    st.info("No votes cast in this category yet.")
        # Download button
        with open(votes_path, "rb") as f:
            st.download_button("Download full votes", f, file_name=votes_path.name)
        # Clear votes section
        st.markdown("---")
        st.subheader("Danger Zone: Clear All Votes")
        # Red-styled clear button
        st.markdown(
            "<style>div.clear-button > button {background-color:red;color:white;}</style>",
            unsafe_allow_html=True
        )
        if st.button("Clear All Votes", key="clear", help="This will delete ALL votes permanently:", args=(), kwargs={}, on_click=None, css_class="clear-button"):
            if st.confirm("Are you sure?", key="confirm1"):
                if st.confirm("Are you really really sure?", key="confirm2"):
                    try:
                        votes_path.unlink()
                        st.success("All votes have been cleared.")
                    except Exception as e:
                        st.error(f"Error clearing votes: {e}")
    else:
        st.info("No votes recorded yet.")

# Voter view
def show_voter():
    # Prevent double voting
    votes_path = find_file(VOTE_FILE)
    voted_already = False
    if votes_path and votes_path.exists():
        try:
            existing = pd.read_csv(votes_path, dtype=str)
            if 'code' in existing.columns and code in existing['code'].tolist():
                voted_already = True
        except pd.errors.EmptyDataError:
            voted_already = False
        except Exception as e:
            st.error(f"Error checking previous votes: {e}")
            st.stop()
    if voted_already:
        st.warning("Our records show you've already voted. Thank you!")
        st.stop()

    st.success("Welcome! Please cast your vote for each category.")
    vote_data = {"code": code}
    errors = []
    # Show all categories upfront
    for cat, (xlsx, csv) in CANDIDATE_FILES.items():
        st.subheader(cat)
        df = load_candidates(xlsx, csv)
        if df.empty:
            st.warning(f"No candidate data for {cat}.")
            continue
        subs = df.columns.tolist()
        choice_sub = st.selectbox(f"Select subcategory for {cat}", ["-- Select --"] + subs, key=f"sub_{cat}")
        sub_opts = df[choice_sub].dropna().tolist() if choice_sub != "-- Select --" else []
        choice_cand = st.selectbox(f"Select candidate for {cat}", ["-- Select --"] + sub_opts, key=f"cand_{cat}")
        if choice_sub == "-- Select --":
            errors.append(f"Please choose a subcategory for {cat}.")
        if choice_cand == "-- Select --":
            errors.append(f"Please choose a candidate for {cat}.")
        else:
            vote_data[cat] = choice_cand
    if st.button("Submit Vote"):
        if errors:
            st.error("\n".join(errors))
        else:
            try:
                new_df = pd.DataFrame([vote_data])
                out_path = votes_path if votes_path else Path(VOTE_FILE)
                new_df.to_csv(out_path, mode="a" if out_path.exists() else "w", header=not out_path.exists(), index=False)
                st.experimental_set_query_params(thanks="1")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error saving vote: {e}")

# Main logic
if code == ADMIN_CODE:
    show_admin()
elif code in df_codes:
    show_voter()
else:
    st.error("Invalid code.")



