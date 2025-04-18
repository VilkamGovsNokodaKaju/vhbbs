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

# --- Session State Initialization ---------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "code" not in st.session_state:
    st.session_state.code = ""
if "error" not in st.session_state:
    st.session_state.error = ""

# --- Helpers --------------------------------------------------------------------
def reset_session():
    st.session_state.page = "login"
    st.session_state.code = ""
    st.session_state.error = ""


def find_file(name: str) -> Path | None:
    p = Path(name)
    if p.exists():
        return p
    for f in Path().iterdir():
        if f.name.lower() == name.lower():
            return f
    return None


def load_codes() -> list[str]:
    for fname in ("codes.csv", "codes.xlsx"):
        path = find_file(fname)
        if path:
            try:
                df = (pd.read_csv(path, header=None, dtype=str)
                      if path.suffix.lower() == ".csv"
                      else pd.read_excel(path, header=None, dtype=str))
                return df.iloc[:, 0].str.strip().tolist()
            except Exception as e:
                st.error(f"Error loading codes from {path.name}: {e}")
    st.error("No codes file found (codes.csv or codes.xlsx).")
    return []


def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
    for fname in (csv_name, xlsx_name):
        path = find_file(fname)
        if path:
            try:
                df = (pd.read_csv(path, dtype=str)
                      if path.suffix.lower() == ".csv"
                      else pd.read_excel(path, dtype=str))
                return df.dropna(axis=1, how="all")
            except Exception as e:
                st.error(f"Error loading {path.name}: {e}")
    st.error(f"No candidate file for {xlsx_name} or {csv_name}.")
    return pd.DataFrame()

# Load valid codes
VALID_CODES = load_codes()

# --- UI ------------------------------------------------------------------------
st.title("Simple Voting Service")

# --- Login Page ---------------------------------------------------------------
if st.session_state.page == "login":
    with st.form("login_form"):
        st.text_input("Enter your 5-character code:", key="code")
        submitted = st.form_submit_button("Login")
    if submitted:
        code = st.session_state.code.strip()
        if code == ADMIN_CODE:
            st.session_state.page = "admin"
            st.session_state.error = ""
        elif code in VALID_CODES:
            # check for repeat vote
            if VOTE_FILE.exists():
                try:
                    existing = pd.read_csv(VOTE_FILE, dtype=str)
                    if 'code' in existing.columns and code in existing['code'].tolist():
                        st.session_state.error = "You have already voted."
                    else:
                        st.session_state.page = "vote"
                        st.session_state.error = ""
                except Exception:
                    st.session_state.page = "vote"
                    st.session_state.error = ""
            else:
                st.session_state.page = "vote"
                st.session_state.error = ""
        else:
            st.session_state.error = "Invalid code."
        st.experimental_rerun()
    if st.session_state.error:
        st.error(st.session_state.error)
    st.stop()

# --- Admin Dashboard ----------------------------------------------------------
if st.session_state.page == "admin":
    st.header("Admin Dashboard")
    if VOTE_FILE.exists() and VOTE_FILE.stat().st_size > 0:
        try:
            votes_df = pd.read_csv(VOTE_FILE, dtype=str)
            for cat in CANDIDATE_FILES.keys():
                st.subheader(f"Top 10 for {cat}")
                if cat in votes_df.columns:
                    counts = votes_df[cat].value_counts().head(10)
                    if not counts.empty:
                        st.table(counts.rename_axis('Candidate').reset_index(name='Votes'))
                    else:
                        st.info("No votes cast in this category yet.")
                else:
                    st.info("No votes cast in this category yet.")
        except Exception:
            st.info("No votes recorded yet.")
    else:
        st.info("No votes recorded yet.")
    st.download_button("Download full votes", open(VOTE_FILE, 'rb'), file_name=VOTE_FILE.name)
    st.markdown("---")
    if st.button("Logout"):
        reset_session()
        st.experimental_rerun()
    st.stop()

# --- Voting Page --------------------------------------------------------------
if st.session_state.page == "vote":
    st.success("Welcome! Please cast your vote for each category.")
    with st.form("vote_form"):
        vote = {'code': st.session_state.code.strip()}
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
            else:
                vote[cat] = chosen_cand
        submitted = st.form_submit_button("Submit Vote")
        if submitted:
            if errors:
                st.error("\n".join(errors))
            else:
                try:
                    pd.DataFrame([vote]).to_csv(
                        VOTE_FILE,
                        mode="a" if VOTE_FILE.exists() else "w",
                        header=not VOTE_FILE.exists(),
                        index=False
                    )
                    st.session_state.page = "thanks"
                except Exception as e:
                    st.error(f"Error saving vote: {e}")
            st.experimental_rerun()
    st.stop()

# --- Thank You Page -----------------------------------------------------------
if st.session_state.page == "thanks":
    st.header("Thank You!")
    st.write("Your vote has been successfully recorded.")
    if st.button("New session"):
        reset_session()
        st.experimental_rerun()
