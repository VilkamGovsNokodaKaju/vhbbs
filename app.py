import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- Configuration ----------
ADMIN_CODE = "ADMIN123"
CODES_CSV = Path("codes.csv")
CODES_XLSX = Path("codes.xlsx")
VOTES_FILE = Path("votes.csv")
CANDIDATE_FILES = {
    "Kategorija A": ("candidates.xlsx", "candidates.csv"),
    "Kategorija B": ("candidates.xlsx", "candidates.csv"),
}

# ---------- Data Functions ----------
def load_codes() -> list[str]:
    if CODES_CSV.exists():
        try:
            df = pd.read_csv(CODES_CSV, header=None, dtype=str)
            return df.iloc[:,0].str.strip().tolist()
        except Exception as e:
            st.error(f"Error reading {CODES_CSV.name}: {e}")
    if CODES_XLSX.exists():
        try:
            df = pd.read_excel(CODES_XLSX, header=None, dtype=str)
            return df.iloc[:,0].str.strip().tolist()
        except Exception as e:
            st.error(f"Error reading {CODES_XLSX.name}: {e}")
    st.error("Could not load codes. Add codes.csv or codes.xlsx with one code per row.")
    return []


def load_votes() -> pd.DataFrame:
    if VOTES_FILE.exists() and VOTES_FILE.stat().st_size > 0:
        try:
            return pd.read_csv(VOTES_FILE, dtype=str)
        except Exception:
            st.error("Error loading votes.csv.")
            return pd.DataFrame()
    return pd.DataFrame()


def save_vote(user_code: str, selections: dict):
    # Build full record with all categories
    record = {cat: selections.get(cat, "") for cat in CANDIDATE_FILES.keys()}
    record['code'] = user_code
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
    if p_csv.exists():
        try:
            return pd.read_csv(p_csv, dtype=str).dropna(axis=1, how="all")
        except Exception as e:
            st.error(f"Error loading {csv_name}: {e}")
            return pd.DataFrame()
    if p_xlsx.exists():
        try:
            return pd.read_excel(p_xlsx, dtype=str).dropna(axis=1, how="all")
        except Exception as e:
            st.error(f"Error loading {xlsx_name}: {e}")
            return pd.DataFrame()
    st.error(f"No candidate file found for {xlsx_name} or {csv_name}.")
    return pd.DataFrame()

# ---------- Session State ----------
st.session_state.setdefault('authed', False)
st.session_state.setdefault('is_admin', False)
st.session_state.setdefault('user_code', '')

# ---------- UI ----------
st.title("Simple Voting Service")

# --- Login or Admin/Vote Switch ---
if not st.session_state.authed:
    code_input = st.text_input("Enter your 5-character code:")
    if st.button("Login"):
        code = code_input.strip()
        valid_codes = load_codes()
        if code == ADMIN_CODE:
            st.session_state.authed = True
            st.session_state.is_admin = True
        elif code in valid_codes:
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

# --- Admin Panel ---
if st.session_state.is_admin:
    st.header("Admin Dashboard")
    votes_df = load_votes()
    if votes_df.empty:
        st.info("No votes recorded yet.")
    else:
        for category in CANDIDATE_FILES.keys():
            st.subheader(f"Top 10 for {category}")
            if category in votes_df.columns:
                counts = votes_df[category].value_counts().head(10)
                if not counts.empty:
                    df_top = counts.rename_axis('Candidate').reset_index(name='Votes')
                    st.table(df_top)
                else:
                    st.info(f"No votes cast for {category} yet.")
            else:
                st.info(f"No votes cast for {category} yet.")
    if VOTES_FILE.exists():
        st.download_button(
            "Download full votes",
            data=VOTES_FILE.read_bytes(),
            file_name=VOTES_FILE.name
        )
    # Clear votes
    st.markdown("---")
    st.subheader("Danger Zone: Clear All Votes")
    if st.button("Confirm and Clear All Votes"):
        try:
            VOTES_FILE.unlink()
            st.success("All votes have been cleared.")
        except Exception as e:
            st.error(f"Error clearing votes: {e}")
    st.stop()

# --- Voting Form ---
st.header("Cast Your Vote")
selections = {}
errors = []
for category,(xlsx,csv) in CANDIDATE_FILES.items():
    st.subheader(category)
    df = load_candidates(xlsx,csv)
    if df.empty:
        st.warning(f"No candidates available for {category}.")
        errors.append(f"No candidates for {category}.")
        continue
    subcats = df.columns.tolist()
    chosen_sub = st.selectbox(f"Select subcategory for {category}", ["-- Select --"]+subcats, key=f"sub_{category}")
    if chosen_sub == "-- Select --":
        errors.append(f"Select a subcategory for {category}.")
        continue
    options = df[chosen_sub].dropna().tolist()
    chosen_cand = st.selectbox(f"Select candidate for {category}", ["-- Select --"]+options, key=f"cand_{category}")
    if chosen_cand == "-- Select --":
        errors.append(f"Select a candidate for {category}.")
    else:
        selections[category] = chosen_cand

if st.button("Submit Vote"):
    if errors:
        st.error("\n".join(errors))
    else:
        save_vote(st.session_state.user_code, selections)
        st.success("Your vote has been recorded.")
        # reset auth to prevent re-vote
        st.session_state.authed = False
        st.session_state.is_admin = False
        st.session_state.user_code = ''
        st.experimental_rerun()
