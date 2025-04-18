import streamlit as st
import pandas as pd
from pathlib import Path

# Configuration
ADMIN_CODE = "ADMIN123"  # Change to your actual admin code
VOTE_FILE = Path("votes.csv")
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "code_value" not in st.session_state:
    st.session_state.code_value = ""
if "error" not in st.session_state:
    st.session_state.error = ""

# Helpers
def reset_session():
    st.session_state.page = "login"
    st.session_state.code_value = ""
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
                if path.suffix.lower() == ".csv":
                    df = pd.read_csv(path, header=None, dtype=str)
                else:
                    df = pd.read_excel(path, header=None, dtype=str)
                return df.iloc[:, 0].str.strip().tolist()
            except Exception as e:
                st.error(f"Error loading codes from {path.name}: {e}")
    st.error("Could not find codes.csv or codes.xlsx with valid codes.")
    return []


def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
    for fname in (csv_name, xlsx_name):
        path = find_file(fname)
        if path:
            try:
                if path.suffix.lower() == ".csv":
                    df = pd.read_csv(path, dtype=str)
                else:
                    df = pd.read_excel(path, dtype=str)
                return df.dropna(axis=1, how="all")
            except Exception as e:
                st.error(f"Error loading candidates from {path.name}: {e}")
    st.error(f"No candidate file found for {xlsx_name} or {csv_name}.")
    return pd.DataFrame()

# Load codes
df_codes = load_codes()

# App title
st.title("Simple Voting Service")

# Login page
def login_page():
    st.text_input("Enter your 5-character code:", key="code_value")
    if st.button("Login"):
        code = st.session_state.code_value.strip()
        if code == ADMIN_CODE:
            st.session_state.page = "admin"
            st.session_state.error = ""
        elif code in df_codes:
            # check if already voted
            if VOTE_FILE.exists():
                try:
                    voted_df = pd.read_csv(VOTE_FILE, dtype=str)
                    if 'code' in voted_df.columns and code in voted_df['code'].tolist():
                        st.session_state.error = "You've already voted."
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
        st.stop()
    if st.session_state.error:
        st.error(st.session_state.error)

# Admin page
def admin_page():
    st.header("Admin Dashboard")
    if VOTE_FILE.exists() and VOTE_FILE.stat().st_size > 0:
        try:
            df_votes = pd.read_csv(VOTE_FILE, dtype=str)
            cats = [c for c in df_votes.columns if c != 'code']
            if not cats:
                st.info("No votes recorded yet.")
            else:
                for cat in cats:
                    st.subheader(f"Top 10 for {cat}")
                    counts = df_votes[cat].value_counts().head(10)
                    if not counts.empty:
                        df_top = counts.rename_axis('Candidate').reset_index(name='Votes')
                        st.table(df_top)
                    else:
                        st.info("No votes cast in this category yet.")
        except Exception:
            st.info("Error reading votes; no data to display.")
    else:
        st.info("No votes recorded yet.")

    st.download_button("Download full votes", open(VOTE_FILE, 'rb'), file_name=VOTE_FILE.name)
    if st.button("Logout"):
        reset_session()
        st.stop()

# Voting page
def vote_page():
    st.success("Welcome! Cast your vote for each category.")
    vote_data = {'code': st.session_state.code_value.strip()}
    errors = []
    for cat, (xlsx, csv) in CANDIDATE_FILES.items():
        st.subheader(cat)
        df = load_candidates(xlsx, csv)
        if df.empty:
            errors.append(f"No data for {cat}.")
            continue
        subcats = df.columns.tolist()
        chosen_sub = st.selectbox(f"Subcategory ({cat}):", ["-- Select --"] + subcats, key=f"sub_{cat}")
        options = df[chosen_sub].dropna().tolist() if chosen_sub != "-- Select --" else []
        chosen_cand = st.selectbox(f"Candidate ({cat}):", ["-- Select --"] + options, key=f"cand_{cat}")
        if chosen_sub == "-- Select --":
            errors.append(f"Select subcategory for {cat}.")
        if chosen_cand == "-- Select --":
            errors.append(f"Select candidate for {cat}.")
        else:
            vote_data[cat] = chosen_cand

    if st.button("Submit Vote"):
        if errors:
            st.error("\n".join(errors))
        else:
            try:
                pd.DataFrame([vote_data]).to_csv(VOTE_FILE, mode="a" if VOTE_FILE.exists() else "w", header=not VOTE_FILE.exists(), index=False)
                st.session_state.page = "thankyou"
                st.stop()
            except Exception as e:
                st.error(f"Error saving vote: {e}")

# Thank you page
def thankyou_page():
    st.header("Thank You!")
    st.write("Your vote has been recorded.")
    if st.button("New Session"):
        reset_session()
        st.stop()

# Render pages
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "admin":
    admin_page()
elif st.session_state.page == "vote":
    vote_page()
elif st.session_state.page == "thankyou":
    thankyou_page()
else:
    reset_session()