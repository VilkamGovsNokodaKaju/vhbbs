###############################################################################
# app.py  –  Excel‑based Streamlit voting service (dupe‑proof, working wipe)
###############################################################################
import streamlit as st
import pandas as pd
from pathlib import Path

# ─────────── CONFIG ──────────────────────────────────────────────────────────
ADMIN_PASSWORD = "change-me"                  # admin secret

POSITIONS = ["pozA", "pozB"]                  # add more positions any time
CANDIDATE_FILES = {                           # one Excel file per position
    "pozA": "candidates.xlsx",
    "pozB": "candidatesB.xlsx",
}

CODES_XLSX = Path("codes.xlsx")               # one code per row
VOTES_CSV  = Path("votes.csv")                # auto‑created

# ─────────── HELPERS ─────────────────────────────────────────────────────────
def load_codes() -> set[str]:
    if not CODES_XLSX.exists():
        st.error("codes.xlsx not found."); return set()
    df = pd.read_excel(CODES_XLSX, header=None, dtype=str)
    return set(df.iloc[:, 0].str.strip())

def load_candidates(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists(): return pd.DataFrame()
    df = pd.read_excel(p, dtype=str)
    return df.dropna(axis=1, how="all")

def load_votes() -> pd.DataFrame:
    if VOTES_CSV.exists() and VOTES_CSV.stat().st_size:
        return pd.read_csv(VOTES_CSV, dtype=str)
    return pd.DataFrame()

def save_vote(record: dict[str, str]) -> None:
    pd.DataFrame([record]).to_csv(
        VOTES_CSV,
        mode="a" if VOTES_CSV.exists() else "w",
        header=not VOTES_CSV.exists(),
        index=False,
    )

# ─────────── SESSION STATE ───────────────────────────────────────────────────
st.session_state.setdefault("mode", "login")      # login | vote | admin
st.session_state.setdefault("user_code", "")
st.session_state.setdefault("wipe_step", 0)       # 0→not started, 1→confirm

# ─────────── LOGIN ───────────────────────────────────────────────────────────
if st.session_state.mode == "login":
    st.title("Secure Voting")
    code = st.text_input("5‑character code")
    if st.button("Login"):
        code = code.strip()
        if code == ADMIN_PASSWORD:
            st.session_state.mode = "admin"
        elif code in load_codes():
            if code in load_votes().get("code", []):   # ❶ DUPLICATE CHECK
                st.error("That code has already voted.")
            else:
                st.session_state.mode = "vote"
                st.session_state.user_code = code
        else:
            st.error("Invalid code.")
    st.stop()

# ─────────── ADMIN PANEL ─────────────────────────────────────────────────────
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
                if top.empty:
                    st.info("No votes for this position yet.")
                else:
                    st.table(top.rename_axis("Candidate").reset_index(name="Votes"))
            else:
                st.info("No votes for this position yet.")

    # Download votes
    if VOTES_CSV.exists():
        st.download_button("Download raw CSV", VOTES_CSV.read_bytes(), "votes.csv")

    # Danger‑zone wipe (two clicks)
    st.markdown("---")
    st.subheader("Danger Zone – wipe ALL votes")
    if st.session_state.wipe_step == 0:
        if st.button("Clear all votes"):
            st.session_state.wipe_step = 1
    elif st.session_state.wipe_step == 1:
        st.warning("Are you sure? This cannot be undone.")
        col1, col2 = st.columns(2)
        if col1.button("Yes, delete"):
            VOTES_CSV.unlink(missing_ok=True)
            st.success("All votes cleared.")
            st.session_state.wipe_step = 0
        if col2.button("Cancel"):
            st.session_state.wipe_step = 0
    st.stop()

# ─────────── VOTING FORM ─────────────────────────────────────────────────────
if st.session_state.mode == "vote":
    st.title("Cast your vote")
    selections, errors = {}, []
    for pos in POSITIONS:
        st.subheader(pos)
        df = load_candidates(CANDIDATE_FILES[pos])
        if df.empty:
            st.error(f"No file for {pos}."); st.stop()
        sub = st.selectbox("Sub‑category", [""]+df.columns.tolist(), key=f"s_{pos}")
        if not sub:
            errors.append(f"Choose sub‑category for {pos}"); continue
        cand = st.selectbox("Candidate", [""]+df[sub].dropna().tolist(), key=f"c_{pos}")
        if not cand:
            errors.append(f"Choose candidate for {pos}")
        else:
            selections[pos] = cand
    if st.button("Submit vote"):
        if errors:
            st.error(" • ".join(errors))
        else:
            save_vote({"code": st.session_state.user_code, **selections})
            st.success("Your vote was saved. Thank you!")
            st.session_state.mode = "login"      # back to login
###############################################################################
