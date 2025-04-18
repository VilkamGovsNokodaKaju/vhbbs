import streamlit as st
import pandas as pd
from pathlib import Path

# ------------------- Configuration -------------------
ADMIN_CODE = "ADMIN123"
VOTE_FILE = Path("votes.csv")
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

# ------------------- Session State -------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "input_code" not in st.session_state:
    st.session_state.input_code = ""
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = 0

# ------------------- Helpers -------------------
def reset_session():
    st.session_state.page = "login"
    st.session_state.input_code = ""
    st.session_state.confirm_clear = 0


def load_codes():
    for fname in ("codes.csv", "codes.xlsx"):
        p = Path(fname)
        if p.exists():
            try:
                if p.suffix.lower() == ".csv":
                    df = pd.read_csv(p, header=None, dtype=str)
                else:
                    df = pd.read_excel(p, header=None, dtype=str)
                return df.iloc[:, 0].str.strip().tolist()
            except Exception as e:
                st.error(f"Error reading {p.name}: {e}")
                return []
    st.error("Could not find a codes file.")
    return []


def load_votes():
    if VOTE_FILE.exists() and VOTE_FILE.stat().st_size > 0:
        try:
            return pd.read_csv(VOTE_FILE, dtype=str)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_vote(record: dict):
    df = pd.DataFrame([record])
    header = not VOTE_FILE.exists()
    df.to_csv(VOTE_FILE, mode="a", header=header, index=False)

# ------------------- Load Data -------------------
valid_codes = load_codes()

# ------------------- Pages -------------------

def login_page():
    st.title("Login")
    st.session_state.input_code = st.text_input("5-character code", st.session_state.input_code)
    if st.button("Login"):
        code = st.session_state.input_code.strip()
        if code == ADMIN_CODE:
            st.session_state.page = "admin"
        elif code in valid_codes:
            votes = load_votes()
            if 'code' in votes.columns and code in votes['code'].tolist():
                st.error("You have already voted.")
            else:
                st.session_state.page = "vote"
                st.session_state.code = code
        else:
            st.error("Invalid code.")
    st.stop()


def vote_page():
    st.title("Vote")
    st.write("Please cast your vote below.")
    record = {"code": st.session_state.code}
    errors = []
    for cat, (xlsx, csv) in CANDIDATE_FILES.items():
        st.subheader(cat)
        df = None
        if Path(csv).exists():
            df = pd.read_csv(csv, dtype=str)
        elif Path(xlsx).exists():
            df = pd.read_excel(xlsx, dtype=str)
        if df is None or df.empty:
            st.warning(f"No candidates for {cat}.")
            errors.append(f"No candidates for {cat}.")
            continue
        subcats = df.columns.tolist()
        choice_sub = st.selectbox(f"Subcategory ({cat})", ["-- Select --"] + subcats, key=f"sub_{cat}")
        if choice_sub == "-- Select --":
            errors.append(f"Select a subcategory for {cat}.")
            continue
        candidates = df[choice_sub].dropna().tolist()
        choice_cand = st.selectbox(f"Candidate ({cat})", ["-- Select --"] + candidates, key=f"cand_{cat}")
        if choice_cand == "-- Select --":
            errors.append(f"Select a candidate for {cat}.")
        else:
            record[cat] = choice_cand
    if st.button("Submit Vote"):
        if errors:
            st.error("\n".join(errors))
        else:
            save_vote(record)
            st.session_state.page = "thankyou"
    st.stop()


def thankyou_page():
    st.title("Thank You!")
    st.write("Your vote has been recorded.")
    if st.button("New Session"):
        reset_session()
    st.stop()


def admin_page():
    st.title("Admin Dashboard")
    votes = load_votes()
    if votes.empty:
        st.info("No votes recorded yet.")
    else:
        for cat in CANDIDATE_FILES.keys():
            st.subheader(f"Top 10 for {cat}")
            if cat in votes.columns:
                top10 = votes[cat].value_counts().head(10)
                if not top10.empty:
                    df_top = top10.rename_axis('Candidate').reset_index(name='Votes')
                    st.table(df_top)
                else:
                    st.info(f"No votes cast for {cat} yet.")
            else:
                st.info(f"No votes cast for {cat} yet.")
    st.download_button("Download full votes", data=VOTE_FILE.read_bytes(), file_name=VOTE_FILE.name)

    st.markdown("---")
    st.subheader("Danger Zone: Clear All Votes")
    if st.session_state.confirm_clear == 0:
        if st.button("Clear All Votes"):
            st.session_state.confirm_clear = 1
    elif st.session_state.confirm_clear == 1:
        st.warning("Are you sure you want to delete all votes?")
        if st.button("Yes, delete all votes", key="confirm_clear_yes"):
            try:
                VOTE_FILE.unlink()
                st.success("All votes have been cleared.")
            except Exception as e:
                st.error(f"Error clearing votes: {e}")
            st.session_state.confirm_clear = 0
        if st.button("Cancel", key="confirm_clear_no"):
            st.session_state.confirm_clear = 0

    if st.button("Logout"):
        reset_session()
    st.stop()

# ------------------- Router -------------------
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "vote":
    vote_page()
elif st.session_state.page == "thankyou":
    thankyou_page()
elif st.session_state.page == "admin":
    admin_page()
else:
    reset_session()
