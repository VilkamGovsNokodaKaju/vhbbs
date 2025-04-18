###############################################################################
# app.py  –  Minimal Streamlit voting service
###############################################################################
import streamlit as st
import pandas as pd
from pathlib import Path

# ───────────────── CONFIGURATION ──────────────────────────────────────────────
ADMIN_PASSWORD = "change-me"                  # secret for your admin panel

POSITIONS = ["pozA", "pozB"]                  # list all positions here

CANDIDATE_FILES = {                           # one file per position
    "pozA": "candidates.csv",                 # first row = subcats, rows below = candidates
    "pozB": "candidatesB.csv",
}

CODES_CSV  = Path("codes.csv")                # one code per row
VOTES_CSV  = Path("votes.csv")                # created automatically
# ───────────────── HELPER FUNCTIONS ───────────────────────────────────────────
def load_codes() -> set[str]:
    return set(pd.read_csv(CODES_CSV, header=None, squeeze=True).str.strip())

def load_candidates(file: str) -> pd.DataFrame:
    p = Path(file)
    if not p.exists(): return pd.DataFrame()
    df = pd.read_csv(p) if p.suffix.lower() == ".csv" else pd.read_excel(p)
    return df.dropna(axis=1, how="all")

def load_votes() -> pd.DataFrame:
    if VOTES_CSV.exists() and VOTES_CSV.stat().st_size:
        return pd.read_csv(VOTES_CSV, dtype=str)
    return pd.DataFrame()

def save_vote(row: dict[str,str]) -> None:
    pd.DataFrame([row]).to_csv(
        VOTES_CSV,
        mode="a" if VOTES_CSV.exists() else "w",
        header=not VOTES_CSV.exists(),
        index=False,
    )
# ───────────────── SESSION STATE SETUP ────────────────────────────────────────
st.session_state.setdefault("mode", "login")      # login • vote • admin
st.session_state.setdefault("user_code", "")
# ───────────────── LOGIN SCREEN ───────────────────────────────────────────────
if st.session_state.mode == "login":
    st.title("Secure Voting")
    code = st.text_input("5‑character code")
    if st.button("Login"):
        code = code.strip()
        if code == ADMIN_PASSWORD:
            st.session_state.mode = "admin"
        elif code in load_codes():
            if code in load_votes().get("code", []):
                st.error("That code has already been used – you can’t vote twice.")
            else:
                st.session_state.mode = "vote"
                st.session_state.user_code = code
        else:
            st.error("Invalid code.")
    st.stop()
# ───────────────── ADMIN PANEL ────────────────────────────────────────────────
if st.session_state.mode == "admin":
    st.title("Admin Dashboard")
    votes = load_votes()
    if votes.empty:
        st.info("No votes recorded yet.")
    else:
        for pos in POSITIONS:
            st.subheader(f"Top 7 for {pos}")
            if pos in votes.columns:
                top = votes[pos].value_counts().head(7)
                st.table(top.rename_axis("Candidate").reset_index(name="Votes"))
            else:
                st.info("No votes yet.")
    if VOTES_CSV.exists():
        st.download_button("Download raw CSV", VOTES_CSV.read_bytes(), "votes.csv")

    st.markdown("---")
    st.subheader("Danger Zone – wipe ALL votes")
    if st.button("Clear votes"):
        if st.button("Really clear votes?"):
            if st.button("YES – DELETE EVERYTHING"):
                VOTES_CSV.unlink(missing_ok=True)
                st.success("All votes cleared.")
    st.stop()
# ───────────────── VOTING FORM ────────────────────────────────────────────────
if st.session_state.mode == "vote":
    st.title("Cast your vote")
    selections: dict[str, str] = {}
    errors = []
    for pos in POSITIONS:
        st.subheader(pos)
        df = load_candidates(CANDIDATE_FILES[pos])
        if df.empty():
            st.error(f"No candidate file for {pos}.")
            st.stop()
        subcat = st.selectbox("Sub‑category", [""] + df.columns.tolist(), key=f"s_{pos}")
        if not subcat:
            errors.append(f"Choose a sub‑category for {pos}")
            continue
        cand = st.selectbox("Candidate", [""] + df[subcat].dropna().tolist(), key=f"c_{pos}")
        if not cand:
            errors.append(f"Choose a candidate for {pos}")
        else:
            selections[pos] = cand
    if st.button("Submit vote"):
        if errors:
            st.error(" • ".join(errors))
        else:
            save_vote({"code": st.session_state.user_code, **selections})
            st.success("Thanks – your vote was saved.")
            st.session_state.mode = "login"
###############################################################################
