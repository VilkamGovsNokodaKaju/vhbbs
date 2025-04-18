import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- Configuration ----------
ADMIN_CODE = "ADMIN123"
CODES_FILE = Path("codes.csv")
VOTES_FILE = Path("votes.csv")
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

# ---------- Data Loaders ----------
@st.cache_data
def load_codes():
    if CODES_FILE.exists():
        try:
            df = pd.read_csv(CODES_FILE, header=None, dtype=str)
            return df.iloc[:,0].str.strip().tolist()
        except Exception:
            pass
    xlsx = CODES_FILE.with_suffix('.xlsx')
    if xlsx.exists():
        try:
            df = pd.read_excel(xlsx, header=None, dtype=str)
            return df.iloc[:,0].str.strip().tolist()
        except Exception:
            pass
    st.error("Unable to load codes. Ensure codes.csv or codes.xlsx is present.")
    return []

@st.cache_data
def load_candidates(xlsx_name, csv_name):
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
        st.error(f"Error loading {xlsx_name}/{csv_name}: {e}")
        return pd.DataFrame()

@st.cache_data
def load_votes():
    if VOTES_FILE.exists() and VOTES_FILE.stat().st_size>0:
        try:
            return pd.read_csv(VOTES_FILE, dtype=str)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# ---------- Save Vote ----------
def save_vote(record: dict):
    df = pd.DataFrame([record])
    df.to_csv(VOTES_FILE, mode='a' if VOTES_FILE.exists() else 'w', header=not VOTES_FILE.exists(), index=False)

# ---------- Main UI ----------
st.title("Simple Voting Service")

# Authentication state
if 'authed' not in st.session_state:
    st.session_state.authed = False
    st.session_state.is_admin = False

# Login form
st.session_state.code_input = st.text_input("Enter your 5-character code:", st.session_state.get('code_input',''))
if st.button("Login"):
    code = st.session_state.code_input.strip()
    valid_codes = load_codes()
    if code == ADMIN_CODE:
        st.session_state.authed = True
        st.session_state.is_admin = True
    elif code in valid_codes:
        # check repeat vote
        votes = load_votes()
        if 'code' in votes.columns and code in votes['code'].tolist():
            st.error("You have already voted.")
        else:
            st.session_state.authed = True
            st.session_state.is_admin = False
            st.session_state.user_code = code
    else:
        st.error("Invalid code.")

if not st.session_state.authed:
    st.stop()

# Admin panel
if st.session_state.is_admin:
    st.header("Admin Dashboard")
    votes = load_votes()
    if votes.empty:
        st.info("No votes recorded yet.")
    else:
        for cat in CANDIDATE_FILES.keys():
            st.subheader(f"Top 10 for {cat}")
            if cat in votes.columns:
                counts = votes[cat].value_counts().head(10)
                if not counts.empty:
                    df_top = counts.rename_axis('Candidate').reset_index(name='Votes')
                    st.table(df_top)
                else:
                    st.info(f"No votes cast for {cat} yet.")
            else:
                st.info(f"No votes cast for {cat} yet.")
    st.download_button("Download full votes", data=VOTES_FILE.read_bytes() if VOTES_FILE.exists() else b'', file_name=VOTES_FILE.name)
    st.markdown("---")
    st.subheader("Danger Zone: Clear All Votes")
    if st.button("Clear All Votes"):
        if st.button("Confirm clear votes", key="clear_yes"):
            try:
                VOTES_FILE.unlink()
                st.success("All votes cleared.")
            except Exception as e:
                st.error(f"Error clearing votes: {e}")
    st.button("Logout", on_click=lambda: reset_session())
    st.stop()

# Voting form
st.header("Cast Your Vote")
votes = load_votes()
record = {'code': st.session_state.user_code}
errors = []
for cat,(xlsx,csv) in CANDIDATE_FILES.items():
    st.subheader(cat)
    df = load_candidates(xlsx,csv)
    if df.empty:
        st.warning(f"No candidates for {cat}.")
        continue
    subcats = df.columns.tolist()
    choice_sub = st.selectbox(f"Subcategory for {cat}", ["-- Select --"]+subcats, key=f"sub_{cat}")
    if choice_sub=="-- Select --":
        errors.append(f"Select subcategory for {cat}.")
        continue
    opts = df[choice_sub].dropna().tolist()
    choice_cand = st.selectbox(f"Choose candidate for {cat}", ["-- Select --"]+opts, key=f"cand_{cat}")
    if choice_cand=="-- Select --":
        errors.append(f"Select candidate for {cat}.")
    else:
        record[cat]=choice_cand

if st.button("Submit Vote"):
    if errors:
        st.error("\n".join(errors))
    else:
        save_vote(record)
        st.success("Your vote has been recorded.")
        st.button("Logout & New Session", on_click=lambda: reset_session())

# --------------------------------
