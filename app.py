###############################################################################
# app.py  –  Simple Streamlit voting service
###############################################################################
import streamlit as st
import pandas as pd
from pathlib import Path

# ───────────────── CONFIGURATION ──────────────────────────────────────────────
ADMIN_PASSWORD = "change-me"                  # ← admin secret

POSITIONS = ["pozA", "pozB"]                  # add more when needed

CANDIDATE_FILES = {                           # file per position
    "pozA": "candidates.xlsx",
    "pozB": "candidates.xlsx",
}

CODES_CSV = Path("codes.xlsx")                 # one code per row
VOTES_CSV = Path("votes.xlsx")                 # created by the app

# ───────────────── HELPERS ────────────────────────────────────────────────────
def load_codes() -> set[str]:
    """—all voter codes as a set—"""
    if not CODES_CSV.exists():
        st.error("codes.xlsx not found")
        return set()
    df = pd.read_csv(CODES_CSV, header=None, dtype=str)
    return set(df.iloc[:, 0].str.strip())

def load_candidates(file: str) -> pd.DataFrame:
    p = Path(file)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p) if p.suffix.lower() == ".xlsx" else pd.read_excel(p)
    return df.dropna(axis=1, how="all")

def load_votes() -> pd.DataFrame:
    if VOTES_CSV.exists() and VOTES_CSV.stat().st_size:
        return pd.read_csv(VOTES_CSV, dtype=str)
    return pd.DataFrame()

def save_vote(row: dict[str, str]) -> None:
    pd.DataFrame([row]).to_csv(
        VOTES_CSV,
        mode="a" if VOTES_CSV.exists() else "w",
        header=not VOTES_CSV.exists(),
        index=False,
    )

# ───────────────── SESSION STATE ──────────────────────────────────────────────
st.session_state.setdefault("mode", "login")      # login | vote | admin
st.session_state.setdefault("user_code", "")

# ───────────────── LOGIN ─────────────────────────────────────────────────────
if st.session_state.mode == "login":
    st.title("Secure Voting")
    code_in = st.text_input("5‑character code")
    if st.button("Login"):
        code = code_in.strip()
        if code == ADMIN_PASSWORD:
            st.session_state.mode = "admin"
        elif code in load_codes():
            if code in load_votes().get("code", []):
                st.error("That code has already been used — you can’t vote twice.")
            else:
                st.session_state.user_code = code
                st.session_state.mode = "vote"
        else:
            st.error("Invalid code.")
    st.stop()

# ───────────────── ADMIN PANEL ───────────────────────────────────────────────
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
                if not top.empty:
                    st.table(top.rename_axis("Candidate")
                                   .reset_index(name="Votes"))
                else:
                    st.info("No votes for this position yet.")
            else:
                st.info("No votes for this position yet.")
    # Download
    if VOTES_CSV.exists():
        st.download_button("Download raw CSV",
                           VOTES_CSV.read_bytes(),
                           file_name="votes.xlsx")
    # Clear votes (2‑click warning)
    st.markdown("---")
    if st.button("Clear ALL votes"):
        if st.button("Really clear votes?"):
            if st.button("YES — DELETE EVERYTHING"):
                VOTES_CSV.unlink(missing_ok=True)
                st.success("All votes cleared.")
    st.stop()

# ───────────────── VOTING FORM ───────────────────────────────────────────────
if st.session_state.mode == "vote":
    st.title("Cast your vote")
    selections: dict[str, str] = {}
    errors = []
    for pos in POSITIONS:
        st.subheader(pos)
        df = load_candidates(CANDIDATE_FILES[pos])
        if df.empty:
            errors.append(f"No candidate file for {pos}")
            continue
        sub = st.selectbox("Sub‑category",
                           [""] + df.columns.tolist(),
                           key=f"s_{pos}")
        if not sub:
            errors.append(f"Choose sub‑category for {pos}")
            continue
        cand = st.selectbox("Candidate",
                            [""] + df[sub].dropna().tolist(),
                            key=f"c_{pos}")
        if not cand:
            errors.append(f"Choose candidate for {pos}")
        else:
            selections[pos] = cand
    if st.button("Submit vote"):
        if errors:
            st.error("• " + "\n• ".join(errors))
        else:
            save_vote({"code": st.session_state.user_code, **selections})
            st.success("Your vote was saved. Thank you!")
            st.session_state.mode = "login"          # back to start
###############################################################################
