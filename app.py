import streamlit as st, pandas as pd
from pathlib import Path

"""
Čau! Nelien, kur nevajag! Paldies!
"""

# ────────── CONFIG ──────────────
ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
WIPE_PASSWORD  = st.secrets["auth"]["wipe_password"]

VOTER_CODES = set(st.secrets["codes"]["list"])

CANDIDATE_FILES = {
    #proletariāts
    "Lēdija": "skoleni.xlsx",
    "Ozols": "skoleni.xlsx",
    "Jokupēteris": "skoleni.xlsx",
    "Gaiteņa simpātija": "skoleni.xlsx",
    "Mūžīgais kavētājs": "skoleni.xlsx",
    "Miegamice": "skoleni.xlsx",
    "Vēsais čalis": "skoleni.xlsx",
    "Durasel zaķēns": "skoleni.xlsx",
    "Kultūras ministrs": "skoleni.xlsx",
    "Nākamais prezidents": "skoleni.xlsx",
    #buržuāzija
    "Interesantākā pieeja mācībām": "skolotaji.xlsx",
    "Skolas dvēsele": "skolotaji.xlsx",
    "Iedvesma": "skolotaji.xlsx",
    "Kartotēka": "skolotaji.xlsx",
    "Modes ikona": "skolotaji.xlsx"
}

VOTES_CSV = Path("votes.csv")

# ────────── HELPERS ──────────────────────────────────────────────────────────
def load_candidates(xlsx: str) -> pd.DataFrame:
    p = Path(xlsx)
    if not p.exists():
        return pd.DataFrame()
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
st.session_state.setdefault("page", "login")
st.session_state.setdefault("user_code", "")
st.session_state.setdefault("wipe_step", 0)

# ────────── LOGIN ────────────────────────────────────────────────────────────
if st.session_state.page == "login":
    st.title("Hāgena balva 2025")
    code_in = st.text_input("Unikālais balsošanas kods")
    if st.button("Autentificēties"):
        code = code_in.strip()
        if code == ADMIN_PASSWORD:
            st.session_state.page = "admin"
        elif code in VOTER_CODES:
            votes = load_votes()
            if "code" in votes.columns and code in votes["code"].values:
                st.error("Šis kods jau ticis izmantots!")
            else:
                st.session_state.user_code = code
                st.session_state.page = "vote"
        else:
            st.error("Kods nav atrasts.")
    st.stop()

# ────────── ADMIN PANEL ──────────────────────────────────────────────────────
if st.session_state.page == "admin":
    st.title("Administratora pieeja")
    votes = load_votes()
    if votes.empty:
        st.info("Neviena balss nav reģistrēta")
    else:
        for pos, file in CANDIDATE_FILES.items():
            st.subheader(f"Nominācijā {pos}")
            if pos in votes.columns:
                top = votes[pos].value_counts().head(7)
                if top.empty:
                    st.info("Neviena balss šajā pozīcijā nav reģistrēta")
                else:
                    st.table(top.rename_axis("Kandidāts").reset_index(name="Balsis"))
            else:
                st.info("Neviena balss šajā pozīcijā nav reģistrēta")

    if VOTES_CSV.exists():
        st.download_button(
            "Ielādēt balsis failā votes.csv",
            VOTES_CSV.read_bytes(),
            "votes.csv"
        )

    st.markdown("---")
    st.subheader("Spēlēt Dievu")
    if st.session_state.wipe_step == 0:
        if st.button("Dzēst visus balsošanas datus"):
            st.session_state.wipe_step = 1
    else:
        pwd = st.text_input("Dzēšanas parole", type="password")
        col1, col2 = st.columns(2)
        if col1.button("Apstiprināt"):
            if pwd == WIPE_PASSWORD:
                VOTES_CSV.unlink(missing_ok=True)
                st.success("pliks un nabadzigs pliks un nabadzigs")
            else:
                st.error("Nepareiza dzēšanas parole")
            st.session_state.wipe_step = 0
        if col2.button("Atcelt"):
            st.session_state.wipe_step = 0
    st.stop()

# ────────── VOTING FORM ──────────────────────────────────────────────────────
if st.session_state.page == "vote":
    st.title("Balso!")
    selections, errs = {}, []

    # Skolēnu nominācijas
    st.header("Skolēnu nominācijas")
    for pos, file in CANDIDATE_FILES.items():
        if file != "skoleni.xlsx":
            continue
        st.subheader(pos)
        df = load_candidates(file)
        if df.empty:
            st.error(f"Nav atrasts kandidātu fails {file} for {pos}.")
            continue
        sub = st.selectbox(
            f"{pos}: Meklēt klasē/sadaļā...",
            [""] + df.columns.tolist(),
            key=f"s_{pos}"
        )
        if not sub:
            errs.append(f"Izvēlēties klasi/sadaļu nominācijā {pos}")
            continue
        cand = st.selectbox(
            f"{pos}: Kandidāts",
            [""] + df[sub].dropna().tolist(),
            key=f"c_{pos}"
        )
        if not cand:
            errs.append(f"Izvēlēšana nominācijā {pos}")
        else:
            selections[pos] = cand

    # Skolotāju nominācijas
    st.header("Skolotāju nominācijas")
    for pos, file in CANDIDATE_FILES.items():
        if file != "skolotaji.xlsx":
            continue
        st.subheader(pos)
        df = load_candidates(file)
        if df.empty:
            st.error(f"Nav atrasts kandidātu fails {file} for {pos}.")
            continue
        sub = st.selectbox(
            f"{pos}: Meklēt sadaļā...",
            [""] + df.columns.tolist(),
            key=f"s_{pos}"
        )
        if not sub:
            errs.append(f"Izvēlēties sadaļu nominācijā {pos}")
            continue
        cand = st.selectbox(
            f"{pos}: Kandidāts",
            [""] + df[sub].dropna().tolist(),
            key=f"c_{pos}"
        )
        if not cand:
            errs.append(f"Izvēlēšana nominācijā {pos}")
        else:
            selections[pos] = cand

    if st.button("Iesniegt balsojumu"):
        if errs:
            st.error(" • ".join(errs))
        else:
            save_vote({"code": st.session_state.user_code, **selections})
            st.success("Balss saglabāta! Paldies!")
            st.session_state.page = "login"
