import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- Configuration ----------
ADMIN_CODE = "ADMIN123"
CODES_FILE = Path("codes.csv")
CODES_XLSX = Path("codes.xlsx")
VOTES_FILE = Path("votes.csv")
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

# ---------- Data Functions ----------
def load_codes() -> list[str]:
    if CODES_FILE.exists():
        try:
            df = pd.read_csv(CODES_FILE, header=None, dtype=str)
            return df.iloc[:,0].str.strip().tolist()
        except Exception:
            pass
    if CODES_XLSX.exists():
        try:
            df = pd.read_excel(CODES_XLSX, header=None, dtype=str)
            return df.iloc[:,0].str.strip().tolist()
        except Exception:
            pass
    st.error("Could not load codes. Please provide codes.csv or codes.xlsx in the app folder.")
    return []


def load_votes() -> pd.DataFrame:
    if VOTES_FILE.exists() and VOTES_FILE.stat().st_size > 0:
        try:
            return pd.read_csv(VOTES_FILE, dtype=str)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_vote(record: dict):
    df = pd.DataFrame([record])
    df.to_csv(
        VOTES_FILE,
        mode='a' if VOTES_FILE.exists() else 'w',
        header=not VOTES_FILE.exists(),
        index=False
    )


def load_candidates(xlsx_name: str, csv_name: str) -> pd.DataFrame:
    p_csv = Path(csv_name)
    p_xlsx = Path(xlsx_name)
    try:
        if p_csv.exists():
            df = pd.read_csv(p_csv, dtype=str)
        elif p_xlsx.exists():
            df = pd.read_excel(p_xlsx, dtype=str)
        else:
            return pd.DataFrame()
        return df.dropna(axis=1, how="all")
    except Exception as e:
        st.error(f"Error loading candidates from {xlsx_name}/{csv_name}: {e}")
        return pd.DataFrame()

# ---------- Session State ----------
st.session_state.setdefault('authed', False)
st.session_state.setdefault('is_admin', False)
st.session_state.setdefault('user_code', '')

# ---------- UI ----------
st.title("Simple Voting Service")

# Login
if not st.session_state.authed:
    code_input = st.text_input("Enter your 5-character code:")
    if st.button("Login"):
        code = code_input.strip()
        codes = load_codes()
        if code == ADMIN_CODE:
            st.session_state.authed = True
            st.session_state.is_admin = True
        elif code in codes:
            votes_df = load_votes()
            if 'code' in votes_df.columns and code in votes_df['code'].tolist():
                st.error("You have already voted.")
            else:
                st.session_state.authed = True
                st.session_state.is_admin = False
                st.session_state.user_code = code
        else:
            st.error("Invalid code.")
    st.stop()

# Admin Panel
if st.session_state.is_admin:
    st.header("Admin Dashboard")
    votes_df = load_votes()
    if votes_df.empty:
        st.info("No votes recorded yet.")
    else:
        for category in CANDIDATE_FILES.keys():
            st.subheader(f"Top 10 for {category}")
            if category in votes_df.columns:
                top10 = votes_df[category].value_counts().head(10)
                if not top10.empty:
                    df_top = top10.rename_axis('Candidate').reset_index(name='Votes')
                    st.table(df_top)
                else:
                    st.info(f"No votes cast for {category} yet.")
            else:
                st.info(f"No votes cast for {category} yet.")
    # Download
    if VOTES_FILE.exists():
        st.download_button(
            "Download full votes",
            data=VOTES_FILE.read_bytes(),
            file_name=VOTES_FILE.name
        )
    # Clear votes with two-step confirmation
    st.markdown("---")
    st.subheader("Danger Zone: Clear All Votes")
    if 'clear_step' not in st.session_state:
        st.session_state.clear_step = 0
    if st.session_state.clear_step == 0:
        if st.button("Clear All Votes"):
            st.session_state.clear_step = 1
    elif st.session_state.clear_step == 1:
        st.warning("Are you sure you want to delete all votes?")
        if st.button("Yes, clear votes", key="clear_yes"):
            st.session_state.clear_step = 2
        if st.button("Cancel", key="clear_no"):
            st.session_state.clear_step = 0
    elif st.session_state.clear_step == 2:
        st.error("Really REALLY sure? This CANNOT be undone.")
        if st.button("Yes, DELETE ALL VOTES", key="clear_confirm"):
            try:
                VOTES_FILE.unlink()
                st.success("All votes have been cleared.")
            except Exception as e:
                st.error(f"Error clearing votes: {e}")
            st.session_state.clear_step = 0
        if st.button("Cancel", key="clear_cancel"):
            st.session_state.clear_step = 0
    st.stop()

# Voting Form
st.header("Cast Your Vote")
record = {'code': st.session_state.user_code}
errors = []
for category,(xlsx,csv) in CANDIDATE_FILES.items():
    st.subheader(category)
    df = load_candidates(xlsx,csv)
    if df.empty:
        st.warning(f"No candidates available for {category}.")
        continue
    subcats = df.columns.tolist()
    choice_sub = st.selectbox(f"Select subcategory for {category}", ["-- Select --"] + subcats, key=f"sub_{category}")
    if choice_sub == "-- Select --":
        errors.append(f"Please select a subcategory for {category}.")
        continue
    options = df[choice_sub].dropna().tolist()
    choice_cand = st.selectbox(f"Select candidate for {category}", ["-- Select --"] + options, key=f"cand_{category}")
    if choice_cand == "-- Select --":
        errors.append(f"Please select a candidate for {category}.")
    else:
        record[category] = choice_cand

if st.button("Submit Vote"):
    if errors:
        st.error("\n".join(errors))
    else:
        save_vote(record)
        st.success("Your vote has been recorded.")
        # disable further submissions
        st.session_state.authed = False
        st.session_state.is_admin = False
        st.session_state.user_code = ""
