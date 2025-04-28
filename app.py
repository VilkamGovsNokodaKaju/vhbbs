import streamlit as st, pandas as pd
from pathlib import Path

# ČAU, NELIEN KUR NEVAJAG, PALDIEEEEEEEES!

# ────────── CONFIG ──────────────
ADMIN_PASSWORD = st.secrets["auth"]["admin_password"]
WIPE_PASSWORD  = st.secrets["auth"]["wipe_password"]

VOTER_CODES = set(st.secrets["codes"]["list"])

CANDIDATE_FILES = {
    # proletariāts
    "Lēdija": {"file": "ledija.xlsx", "description": "Šo meiteni neievērot skolas gaiteņis nevar, jo vienmēr būs kāds džentelmenis, kas tai pasniegs roku, lai nepakrīt. Viņa pat 8:00 no rītā, matemātikas stundā spīdēs, jo “slikta matu diena” vai “skolas gaiss” uz viņu neattiecās. Tu vai nu gribi šo dāmu apprecēt, vai kļūt par viņu."},
    "Ozols": {"file": "ozols.xlsx", "description": "Godinām staltāko džeku, kurš, tāpat kā ozols, izceļas ar stingru raksturu, atbildību un spēju stāties pretī jebkādām grūtībām."},
    "Jokupēteris": {"file": "jokupeteris.xlsx", "description": "Šis ir cilvēks, kurš vienmēr spēj uzlabot dienu ar vienu labu joku vai asprātīgu piezīmi. Viņa humors nav tikai smieklīgs – tas saliedē, iepriecina un atgādina, ka arī visnopietnākajos brīžos ir vieta smaidam."},
    "Gaiteņa simpātija": {"file": "simpatija.xlsx", "description": "Tas skolēns, kuru redzot gaiteņos, jāpaskatās divreiz. Kurš simpātiskais garāmgājējs iekarojis tavu sirdi?"},
    "Mūžīgais kavētājs": {"file": "kavetajs.xlsx", "description": "Ja kavēšana būtu māksla, šis cilvēks jau sen būtu ieguvis zelta medaļu. Stundas sākas bez viņa, reizēm arī beidzas bez viņa. Vienmēr ceļā, bet reti galā laikā."},
    "Miegamice": {"file": "miegamice.xlsx", "description": "Godinām skolēnu, kurš stundās visbiežāk dodas sapņu valstībā un spēj iemigt pat visaktīvākajās nodarbībās."},
    "Vēsais čalis": {"file": "vesais.xlsx", "description": "Šis puisis ir īstākā miera un nosvērtības personifikācija. Viņš nekad neuztver neko pārāk nopietni un nezin tādu terminu kā “stress”. Šis zēns ķers uzmanību pat necenšoties un lai gan, parasti komunicē īsos, nepārliešanu teikumos, viņš būs Tavs pats labākais padomdevējs."},
    "Durasel zaķēns": {"file": "zakens.xlsx", "description": "Draugs, kuram pēc desmitās stundas vēl joprojām ir enerģija, allaž uzlādēts un vienmēr gatavs jokoties - īsts “Durasel” bateriju zaķēns."},
    "Kultūras ministrs": {"file": "kultura.xlsx", "description": "Šī nominācija ir domāta skolēnam, kurš ienes kultūru mūsu skolas ikdienā – gan caur radošām idejām, gan reāliem darbiem. Viņš vai viņa ir tas cilvēks, kurš ar aizrautību iesaistās pasākumu veidošanā, liekot mums visiem justies kā daļai no kaut kā īpaša."},
    "Nākamais prezidents": {"file": "prezidents.xlsx", "description": "Šī persona piedzimusi ar līdera gēnu – harizmātiska, pārliecināta un vienmēr ar viedokli. Spēj saliedēt cilvēkus ap sevi un risināt problēmas. Debates? Uzvarētas. Plāns? Vienmēr ir. Ja kāds spēj mainīt pasauli – tad tas ir viņš vai viņa."},
    # buržuāzija
    "Interesantākā pieeja mācībām": {"file": "pieeja.xlsx", "description": "Skolotājs, kas mācību vielu padara ne tikai izzinošu, bet arī jautru. Nominē skolotāju, lai tam izrādītu pateicību par oriģinālākajām stundām."},
    "Skolas dvēsele": {"file": "dvesele.xlsx", "description": "Pedagogs, kura sirds pukst skolas gaitenī kā silta saules stari pavasara rītā, iedvesmojot katru smaidīt."},
    "Iedvesma": {"file": "iedvesma.xlsx", "description": "Vārdi lido kā krāsainas spalvas, kad “Iedvesmas” pasniedzējs ar asprātīgiem stāstiem un drosmīgu attieksmi atver durvis jaunām idejām un liek audzēkņiem pacelties pāri ierastajam."},
    "Kartotēka": {"file": "kartoteka.xlsx", "description": "Vieds cilvēks ar vēl viedākiem vārdiem. Ar skanīgu citātu gēnu apveltīts skolotājs, kas spēj ar savu valodu gan likt redzēt dzīvi no jaunas puses, gan nolikt kādu pie vietas."},
    "Modes ikona": {"file": "mode.xlsx", "description": "Šis skolotājs skolēnu acīm vienmēr pamanāms ar raibāko, radošāko un košāko apģērbu, allaž izzinot vai pat veidojot jaunākās modes tendences."}
}

VOTES_CSV = Path("votes.csv")

# ────────── HELPERS ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_candidates(xlsx: str) -> pd.DataFrame:
    p = Path(xlsx)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_excel(p, dtype=str).dropna(axis=1, how="all")

# Preload both sheets once per session/process
df_skoleni = load_candidates("skoleni.xlsx")
df_skolotaji = load_candidates("skolotaji.xlsx")

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
    for pos, cfg in CANDIDATE_FILES.items():
        if cfg["file"] != "skoleni.xlsx":
            continue
        st.subheader(pos)
        if cfg.get("description"):
            st.write(cfg["description"])
        df = df_skoleni
        if df.empty:
            st.error(f"Nav atrasts kandidātu fails {cfg['file']} for {pos}.")
            continue
        # Flatten all candidates without subsections
        candidates = sorted(df.stack().dropna().unique().tolist())
        cand = st.selectbox(
            f"{pos}: Kandidāts",
            [""] + candidates,
            key=f"c_{pos}"
        )
        if not cand:
            errs.append(f"Izvēlēšana nominācijā {pos}")
        else:
            selections[pos] = cand

    # Skolotāju nominācijas
    st.header("Skolotāju nominācijas")
    for pos, cfg in CANDIDATE_FILES.items():
        if cfg["file"] != "skolotaji.xlsx":
            continue
        st.subheader(pos)
        if cfg.get("description"):
            st.write(cfg["description"])
        df = df_skolotaji
        if df.empty:
            st.error(f"Nav atrasts kandidātu fails {cfg['file']} for {pos}.")
            continue
        # Flatten all candidates without subsections
        candidates = sorted(df.stack().dropna().unique().tolist())
        cand = st.selectbox(
            f"{pos}: Kandidāts",
            [""] + candidates,
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
