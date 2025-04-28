import streamlit as st
import pandas as pd
from pathlib import Path

# ────────── CONFIG & SECRETS ──────────────
VOTES_CSV = Path("votes.csv")
ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
WIPE_PASSWORD  = st.secrets["auth"]["wipe_password"]
VOTER_CODES = {str(c).strip() for c in st.secrets["codes"]["list"]}

# ────────── CANDIDATES ────────────────────────────────────────────────────────
CANDIDATE_FILES = {
    # skolēnu nominācijas
    "Lēdija":             {"file": "ledija.xlsx",      "description": "Šo meiteni neievērot skolas gaiteņis nevar..."},
    "Ozols":              {"file": "ozols.xlsx",       "description": "Godinām staltāko džeku..."},
    "Jokupēteris":        {"file": "jokupeteris.xlsx", "description": "Šis ir cilvēks, kurš vienmēr spēj..."},
    "Gaiteņa simpātija":  {"file": "simpatija.xlsx",    "description": "Tas skolēns, kuru redzot gaiteņos..."},
    "Mūžīgais kavētājs":   {"file": "kavetajs.xlsx",     "description": "Ja kavēšana būtu māksla..."},
    "Miegamice":          {"file": "miegamice.xlsx",    "description": "Godinām skolēnu, kurš stundās..."},
    "Vēsais čalis":       {"file": "vesais.xlsx",       "description": "Šis puisis ir īstākā miera..."},
    "Durasel zaķēns":     {"file": "zakens.xlsx",       "description": "Draugs, kuram pēc desmitās stundas..."},
    "Kultūras ministrs":  {"file": "kultura.xlsx",      "description": "Šī nominācija ir domāta skolēnam..."},
    "Nākamais prezidents": {"file": "prezidents.xlsx",   "description": "Šī persona piedzimusi ar līdera..."},
    # skolotāju nominācijas
    "Interesantākā pieeja mācībām": {"file": "pieeja.xlsx",   "description": "Skolotājs, kas mācību vielu padara..."},
    "Skolas dvēsele":               {"file": "dvesele.xlsx",  "description": "Pedagogs, kura sirds pukst..."},
    "Iedvesma":                     {"file": "iedvesma.xlsx", "description": "Vārdi lido kā krāsainas spalvas..."},
    "Kartotēka":                    {"file": "kartoteka.xlsx","description": "Vieds cilvēks ar vēl viedākiem..."},
    "Modes ikona":                  {"file": "mode.xlsx",      "description": "Šis skolotājs skolēnu acīm..."}
}

# ────────── HELPERS ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_flat_candidates(xlsx: str) -> list[str]:
    p = Path(xlsx)
    if not p.exists():
        return []
    df = pd.read_excel(p, dtype=str).dropna(axis=1, how="all")
    return sorted(df.stack().dropna().unique().tolist())


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
        for pos in CANDIDATE_FILES:
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
    student_positions = ["Lēdija","Ozols","Jokupēteris","Gaiteņa simpātija","Mūžīgais kavētājs","Miegamice","Vēsais čalis","Durasel zaķēns","Kultūras ministrs","Nākamais prezidents"]
    for pos in student_positions:
        cfg = CANDIDATE_FILES[pos]
        st.subheader(pos)
        st.write(cfg["description"])
        candidates = load_flat_candidates(cfg["file"])
        if not candidates:
            st.error(f"Nav atrasts kandidātu fails {cfg['file']} for {pos}.")
            continue
        cand = st.selectbox(f"{pos}: Kandidāts", [""]+candidates, key=f"c_{pos}")
        if not cand:
            errs.append(f"Izvēlēšana nominācijā {pos}")
        else:
            selections[pos] = cand

    # Skolotāju nominācijas
    st.header("Skolotāju nominācijas")
    teacher_positions = ["Interesantākā pieeja mācībām","Skolas dvēsele","Iedvesma","Kartotēka","Modes ikona"]
    for pos in teacher_positions:
        cfg = CANDIDATE_FILES[pos]
        st.subheader(pos)
        st.write(cfg["description"])
        candidates = load_flat_candidates(cfg["file"])
        if not candidates:
            st.error(f"Nav atrasts kandidātu fails {cfg['file']} for {pos}.")
            continue
        cand = st.selectbox(f"{pos}: Kandidāts", [""]+candidates, key=f"c_{pos}")
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
