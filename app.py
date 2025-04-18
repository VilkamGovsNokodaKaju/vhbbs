import streamlit as st, pandas as pd
from pathlib import Path

# ────────── CONFIG ──────────────
ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]  
WIPE_PASSWORD  = st.secrets["auth"]["wipe_password"]    

VOTER_CODES = set(st.secrets["codes"]["list"])           

POSITIONS = ["pozA", "pozB"]
CANDIDATE_FILES = {            
    "pozA": "candidates.xlsx",
    "pozB": "candidates.xlsx",
}

VOTES_CSV = Path("votes.csv")    # created automatically

# ────────── HELPERS ──────────────────────────────────────────────────────────
def load_candidates(xlsx: str) -> pd.DataFrame:
    p = Path(xlsx)
    if not p.exists(): return pd.DataFrame()
    return pd.read_excel(p, dtype=str).dropna(axis=1, how="all")

def load_votes() -> pd.DataFrame:
    if VOTES_CSV.exists() and VOTES_CSV.stat().st_size:
        return pd.read_csv(VOTES_CSV, dtype=str)
    return pd.DataFrame()

def save_vote(row: dict):
    pd.DataFrame([row]).to_csv(
        VOTES_CSV,
        mode="a" if VOTES_CSV.exists() else "w",
        header=not VOTES_CSV.exists(),
        index=False,
    )

# ────────── SESSION STATE ────────────────────────────────────────────────────
st.session_state.setdefault("page", "login")     # login | vote | admin
st.session_state.setdefault("user_code", "")
st.session_state.setdefault("wipe_step", 0)

# ────────── LOGIN ────────────────────────────────────────────────────────────
if st.session_state.page == "login":
    st.title("Secure Voting")
    code_in = st.text_input("5‑character code")
    if st.button("Login"):
        code = code_in.strip()
        if code == ADMIN_PASSWORD:
            st.session_state.page = "admin"
        elif code in VOTER_CODES:
            votes = load_votes()
            if "code" in votes.columns and code in votes["code"].values:
                st.error("That code has already voted.")
            else:
                st.session_state.user_code = code
                st.session_state.page = "vote"
        else:
            st.error("Invalid code.")
    st.stop()

# ────────── ADMIN PANEL ──────────────────────────────────────────────────────
if st.session_state.page == "admin":
    st.title("Admin Dashboard")
    votes = load_votes()
    if votes.empty:
        st.info("No votes recorded yet.")
    else:
        for pos in POSITIONS:
            st.subheader(f"Top 7 for {pos}")
            if pos in votes.columns:
                top = votes[pos].value_counts().head(7)
                if top.empty:
                    st.info("No votes for this position yet.")
                else:
                    st.table(top.rename_axis("Candidate").reset_index(name="Votes"))
            else:
                st.info("No votes for this position yet.")

    if VOTES_CSV.exists():
        st.download_button("Download votes.csv", VOTES_CSV.read_bytes(), "votes.csv")

    st.markdown("---")
    st.subheader("Danger Zone – wipe ALL votes")
    if st.session_state.wipe_step == 0:
        if st.button("Clear votes"):
            st.session_state.wipe_step = 1
    elif st.session_state.wipe_step == 1:
        pwd = st.text_input("Wipe password", type="password")
        col1, col2 = st.columns(2)
        if col1.button("CONFIRM"):
            if pwd == WIPE_PASSWORD:
                VOTES_CSV.unlink(missing_ok=True)
                st.success("All votes cleared.")
            else:
                st.error("Wrong wipe password.")
            st.session_state.wipe_step = 0
        if col2.button("Cancel"):
            st.session_state.wipe_step = 0
    st.stop()

# ────────── VOTING FORM ──────────────────────────────────────────────────────
if st.session_state.page == "vote":
    st.title("Cast your vote")
    selections, errs = {}, []
    for pos in POSITIONS:
        st.subheader(pos)
        df = load_candidates(CANDIDATE_FILES[pos])
        if df.empty:
            st.error(f"No candidate file for {pos}."); st.stop()
        sub = st.selectbox("Sub‑category", [""]+df.columns.tolist(), key=f"s_{pos}")
        if not sub:
            errs.append(f"Pick sub‑category for {pos}"); continue
        cand = st.selectbox("Candidate", [""]+df[sub].dropna().tolist(), key=f"c_{pos}")
        if not cand:
            errs.append(f"Pick candidate for {pos}")
        else:
            selections[pos] = cand
    if st.button("Submit vote"):
        if errs:
            st.error(" • ".join(errs))
        else:
            save_vote({"code": st.session_state.user_code, **selections})
            st.success("Vote saved. Thank you!")
            st.session_state.page = "login" 

