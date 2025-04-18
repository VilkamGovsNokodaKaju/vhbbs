import streamlit as st
import pandas as pd
from pathlib import Path

# ────────── CONFIG ──────────────────────────────────
ADMIN_PASSWORD = st.secrets.get("auth", {}).get("admin_password", "change-me")
WIPE_PASSWORD  = st.secrets.get("auth", {}).get("wipe_password",  "extra-secret")

POSITIONS = ["pozA", "pozB"]

CANDIDATE_FILES = {
    "pozA": "candidates.xlsx",
    "pozB": "candidatesB.xlsx",
}

CODES_XLSX = Path("codes.xlsx")
VOTES_CSV  = Path("votes.csv")

# ────────── HELPERS ──────────────────────────────────────────────────────────
def load_codes() -> set[str]:
    if not CODES_XLSX.exists():
        st.error("codes.xlsx not found."); return set()
    return set(pd.read_excel(CODES_XLSX, header=None, dtype=str)[0].str.strip())

def load_candidates(file: str) -> pd.DataFrame:
    p = Path(file)
    if not p.exists(): return pd.DataFrame()
    return pd.read_excel(p, dtype=str).dropna(axis=1, how="all")

def load_codes() -> set[str]:
    """Read voter codes from Streamlit Secrets."""
    secret_list = st.secrets.get("codes", {}).get("list", [])
    return set(code.strip() for code in secret_list)

def save_vote(row: dict):
    pd.DataFrame([row]).to_csv(
        VOTES_CSV,
        mode="a" if VOTES_CSV.exists() else "w",
        header=not VOTES_CSV.exists(),
        index=False,
    )

# ────────── SESSION STATE ────────────────────────────────────────────────────
st.session_state.setdefault("page", "login")
st.session_state.setdefault("code",    "")
st.session_state.setdefault("wipe_step", 0)

# ────────── LOGIN PAGE ───────────────────────────────────────────────────────
if st.session_state.page == "login":
    st.title("Secure Voting")
    code_in = st.text_input("5‑character code")
    if st.button("Login"):
        code = code_in.strip()
        if code == ADMIN_PASSWORD:
            st.session_state.page = "admin"
        elif code in load_codes():
            if code in load_votes().get("code", []).values:
                st.error("That code has already voted.")
            else:
                st.session_state.code = code
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

    # danger‑zone wipe
    st.markdown("---")
    st.subheader("Danger Zone – wipe ALL votes")
    if st.session_state.wipe_step == 0:
        if st.button("Clear votes"):
            st.session_state.wipe_step = 1
    elif st.session_state.wipe_step == 1:
        pwd = st.text_input("Enter WIPE password", type="password")
        if st.button("Confirm wipe"):
            if pwd == WIPE_PASSWORD:
                VOTES_CSV.unlink(missing_ok=True)
                st.success("All votes cleared.")
            else:
                st.error("Wrong wipe password.")
            st.session_state.wipe_step = 0
        if st.button("Cancel wipe"):
            st.session_state.wipe_step = 0
    st.stop()

# ────────── VOTING FORM ──────────────────────────────────────────────────────
if st.session_state.page == "vote":
    st.title("Cast your vote")
    selections, errors = {}, []
    for pos in POSITIONS:
        st.subheader(pos)
        df = load_candidates(CANDIDATE_FILES[pos])
        if df.empty:
            st.error(f"No candidate file for {pos}.")
            st.stop()
        sub = st.selectbox("Sub‑category", [""]+df.columns.tolist(), key=f"s_{pos}")
        if not sub:
            errors.append(f"Pick sub‑category for {pos}"); continue
        cand = st.selectbox("Candidate", [""]+df[sub].dropna().tolist(), key=f"c_{pos}")
        if not cand:
            errors.append(f"Pick candidate for {pos}")
        else:
            selections[pos] = cand
    if st.button("Submit vote"):
        if errors:
            st.error(" • ".join(errors))
        else:
            save_vote({"code": st.session_state.code, **selections})
            st.success("Vote saved. You may close the page.")
            st.session_state.page = "login"

