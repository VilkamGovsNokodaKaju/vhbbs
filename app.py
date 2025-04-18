import streamlit as st
import pandas as pd
from pathlib import Path

# --- Configuration --------------------------------------------------------------
ADMIN_CODE = "ADMIN123"  # Change to your actual admin code
VOTE_FILE = Path("votes.csv")
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

# Initialize vote flag
if "voted" not in st.session_state:
    st.session_state.voted = False
# Initialize clear_confirm
if "clear_confirm" not in st.session_state:
    st.session_state.clear_confirm = 0

# --- Helpers --------------------------------------------------------------------

def find_file(name: str) -> Path | None:
    """Case-insensitive file finder in app directory."""
    p = Path(name)
    if p.exists(): return p
    for f in Path().iterdir():
        if f.name.lower() == name.lower(): return f
    return None


def load_codes() -> list[str]:
    """Load valid voter codes from codes.csv or codes.xlsx."""
    for fname in ("codes.csv", "codes.xlsx"):
        path = find_file(fname)
        if path:
            try:
                if path.suffix.lower() == ".csv":
                    df = pd.read_csv(path, header=None, dtype=str)
                else:
                    df = pd.read_excel(path, header=None, dtype=str)
                return df.iloc[:, 0].str.strip().tolist()
            except Exception as e:
                st.error(f"Error loading codes from {path.name}: {e}")
    st.error("No codes file found (codes.csv or codes.xlsx).")
    return []


def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
    """Load candidate matrix for a category from CSV or XLSX."""
    for fname in (csv_name, xlsx_name):
        path = find_file(fname)
        if path:
            try:
                df = pd.read_csv(path, dtype=str) if path.suffix.lower() == ".csv" else pd.read_excel(path, dtype=str)
                return df.dropna(axis=1, how="all")
            except Exception as e:
                st.error(f"Error loading {path.name}: {e}")
    st.error(f"No candidate file for {xlsx_name} or {csv_name}.")
    return pd.DataFrame()

# Load valid codes once
df_codes = load_codes()

# --- UI ------------------------------------------------------------------------
st.title("Simple Voting Service")

# Login input
st.text_input("Enter your 5-character code:", key="code_input")
code = st.session_state.get("code_input", "").strip()
if not code:
    st.stop()

# --- Thank-you screen ---------------------------------------------------------
if st.session_state.voted:
    st.header("Thank You!")
    st.write("Your vote has been successfully recorded.")
    if st.button("Back to login"):
        st.session_state.voted = False
        st.session_state.clear_confirm = 0
        st.session_state.code_input = ""
    st.stop()

# --- Admin Dashboard ----------------------------------------------------------
def show_admin():
    st.header("Admin Dashboard")
    # Check if vote file exists and is non-empty
    if VOTE_FILE.exists():
        try:
            if VOTE_FILE.stat().st_size == 0:
                st.info("No votes recorded yet.")
            else:
                votes_df = pd.read_csv(VOTE_FILE, dtype=str)
                cats = [c for c in votes_df.columns if c != 'code']
                if not cats:
                    st.info("No votes recorded yet.")
                else:
                    for cat in cats:
                        st.subheader(f"Top 10 for {cat}")
                        counts = votes_df[cat].value_counts().head(10)
                        if not counts.empty:
                            df_top = counts.rename_axis('Candidate').reset_index(name='Votes')
                            st.table(df_top)
                        else:
                            st.info("No votes cast in this category yet.")
        except pd.errors.EmptyDataError:
            st.info("No votes recorded yet.")
        except Exception as e:
            st.error(f"Error reading votes: {e}")
    else:
        st.info("No votes recorded yet.")

# --- Voter Interface ----------------------------------------------------------
def show_voter():
    # Prevent repeat voting
    if VOTE_FILE.exists():
        try:
            existing = pd.read_csv(VOTE_FILE, dtype=str)
            if code in existing.get('code', []).tolist():
                st.warning("Our records show you've already voted. Thank you!")
                return
        except Exception:
            pass

    st.success("Welcome! Please cast your vote for each category.")
    vote = {'code': code}
    errors = []
    for cat, (xlsx, csv) in CANDIDATE_FILES.items():
        st.subheader(cat)
        df = load_candidates(xlsx, csv)
        if df.empty:
            errors.append(f"No candidate data for {cat}.")
            continue
        subcats = df.columns.tolist()
        chosen_sub = st.selectbox(f"Select subcategory for {cat}", ["-- Select --"] + subcats, key=f"sub_{cat}")
        opts = df[chosen_sub].dropna().tolist() if chosen_sub != "-- Select --" else []
        chosen_cand = st.selectbox(f"Select candidate for {cat}", ["-- Select --"] + opts, key=f"cand_{cat}")
        if chosen_sub == "-- Select --":
            errors.append(f"Choose a subcategory for {cat}.")
        if chosen_cand == "-- Select --":
            errors.append(f"Choose a candidate for {cat}.")
        if chosen_sub != "-- Select --" and chosen_cand != "-- Select --":
            vote[cat] = chosen_cand

    if st.button("Submit Vote"):
        if errors:
            st.error("\n".join(errors))
        else:
            try:
                pd.DataFrame([vote]).to_csv(VOTE_FILE, mode="a" if VOTE_FILE.exists() else "w", header=not VOTE_FILE.exists(), index=False)
                st.session_state.voted = True
            except Exception as e:
                st.error(f"Error saving vote: {e}")

# --- Main Logic ---------------------------------------------------------------
if code == ADMIN_CODE:
    show_admin()
elif code in df_codes:
    show_voter()
else:
    st.error("Invalid code.")
