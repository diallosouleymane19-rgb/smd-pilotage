"""
Dashboard Pilotage SMD — Application Streamlit
SMD Global Consulting LLC
"""

import streamlit as st
import requests
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SMD Pilotage",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

NOTION_VERSION = "2022-06-28"
CRM_DB_ID      = "40fb8514-337d-4550-b899-743383a02169"
DASHBOARD_DB_ID = "ad90d1fd-7f41-400b-97bc-3098faa335a5"
MARKETING_DB_ID = "7abdb6fc-eae3-43de-afd5-71252ab60f0e"
ROUTEUR_WEBHOOK  = "https://hook.eu1.make.com/5hbyls7ztgpvc76avtx06h3gfpbi4u2o"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-sonnet-4-6"

KPI_ICONS = {
    "Cabinets convertis":   "🎉",
    "Dossiers archivés":    "📁",
    "Prospects actifs":     "✉️",
    "Total pipeline CRM":   "📊",
    "Emails envoyés":       "📧",
    "Relance programmée":   "🔁",
    "CA potentiel pipeline": "💰",
}

PRIX_UNITAIRE = 270  # € par micro-audit AI Act

# ─────────────────────────────────────────────
# SECRETS
# ─────────────────────────────────────────────
def get_notion_token():
    try:
        return st.secrets["notion"]["token"]
    except Exception:
        return None

def get_make_api_key():
    try:
        return st.secrets["make"]["api_key"]
    except Exception:
        return None

def get_anthropic_key():
    try:
        return st.secrets["anthropic"]["api_key"]
    except Exception:
        return None

# ─────────────────────────────────────────────
# NOTION HELPERS
# ─────────────────────────────────────────────
def notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

@st.cache_data(ttl=60)
def get_kpi_values(token):
    """Query la DB Dashboard pour récupérer les KPIs."""
    try:
        r = requests.post(
            f"https://api.notion.com/v1/databases/{DASHBOARD_DB_ID}/query",
            headers=notion_headers(token),
            json={"page_size": 10},
            timeout=8,
        )
        if r.status_code != 200:
            return {}
        pages = r.json().get("results", [])
        results = {}
        for page in pages:
            props = page.get("properties", {})
            # Titre = propriété Métrique
            titre_list = props.get("Métrique", {}).get("title", [])
            titre = titre_list[0].get("plain_text", "") if titre_list else ""
            if not titre:
                continue
            valeur_list = props.get("Valeur", {}).get("rich_text", [])
            valeur = valeur_list[0].get("plain_text", "0") if valeur_list else "0"
            semaine_list = props.get("Semaine", {}).get("rich_text", [])
            semaine = semaine_list[0].get("plain_text", "") if semaine_list else ""
            sel = props.get("Statut", {}).get("select")
            statut = sel["name"] if sel else ""
            results[titre] = {"valeur": valeur, "semaine": semaine, "statut": statut}
        return results
    except Exception:
        return {}

@st.cache_data(ttl=60)
def get_crm_prospects(token):
    try:
        r = requests.post(
            f"https://api.notion.com/v1/databases/{CRM_DB_ID}/query",
            headers=notion_headers(token),
            json={"page_size": 50},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=60)
def get_marketing_content(token):
    try:
        r = requests.post(
            f"https://api.notion.com/v1/databases/{MARKETING_DB_ID}/query",
            headers=notion_headers(token),
            json={"page_size": 20},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []

def extract_text(prop):
    if not prop:
        return ""
    for key in ("title", "rich_text"):
        if key in prop and prop[key]:
            return prop[key][0].get("plain_text", "")
    if "select" in prop and prop["select"]:
        return prop["select"].get("name", "")
    if "email" in prop:
        return prop["email"] or ""
    return ""

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 SMD Pilotage")
    st.caption("SMD Global Consulting LLC")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📊 KPIs", "📇 CRM Pipeline", "🤖 Envoyer instruction", "📢 Marketing", "🔬 Rapport IA", "⚙️ Système"],
        label_visibility="collapsed",
    )

    st.divider()
    token = get_notion_token()
    if token:
        st.success("✅ Notion connecté")
    else:
        st.error("❌ Token Notion manquant")

    st.caption(f"Actualisation : {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# PAGE 1 — KPIs
# ─────────────────────────────────────────────
if page == "📊 KPIs":
    st.title("📊 Dashboard KPIs SMD")
    st.caption("Mis à jour automatiquement chaque matin à 8h par Make · Rafraîchissement manuel disponible")

    if not token:
        st.warning("Configure le token Notion dans les secrets Streamlit.")
    else:
        kpis = get_kpi_values(token)

        if not kpis:
            st.warning("Impossible de lire le Dashboard Notion. Vérifie que l'intégration 'Audit RGPD SMD' est connectée à la DB Dashboard Pilotage SMD.")
        else:
            cols = st.columns(4)
            ordre = ["Cabinets convertis", "Dossiers archivés", "Prospects actifs", "Total pipeline CRM"]
            for col, nom in zip(cols, ordre):
                data = kpis.get(nom, {"valeur": "—", "semaine": "", "statut": ""})
                icon = KPI_ICONS.get(nom, "📌")
                with col:
                    st.metric(
                        label=f"{icon} {nom}",
                        value=data["valeur"],
                        delta=f"{data['semaine']} — {data['statut']}" if data["semaine"] else data["statut"],
                        delta_color="normal" if data["statut"] == "OK" else "inverse",
                    )

        # ── Ligne 2 : nouvelles métriques campagne ──
        ordre2 = ["Emails envoyés", "Relance programmée", "CA potentiel pipeline"]
        kpis2_present = [k for k in ordre2 if k in kpis]
        if kpis2_present:
            cols2 = st.columns(len(kpis2_present))
            for col, nom in zip(cols2, kpis2_present):
                data = kpis[nom]
                icon = KPI_ICONS.get(nom, "📌")
                with col:
                    st.metric(
                        label=f"{icon} {nom}",
                        value=data["valeur"],
                        delta=f"{data['semaine']} — {data['statut']}" if data["semaine"] else data["statut"],
                        delta_color="normal" if data["statut"] == "OK" else "inverse",
                    )

        st.divider()

        # ── Performance commerciale ──
        st.subheader("💰 Performance commerciale")
        convertis_raw = kpis.get("Cabinets convertis", {}).get("valeur", "0")
        prospects_raw = kpis.get("Prospects actifs", {}).get("valeur", "0")
        try:
            nb_convertis  = int(convertis_raw)
            nb_prospects   = int(prospects_raw)
            ca_encaisse    = nb_convertis * PRIX_UNITAIRE
            ca_pipeline    = nb_prospects * PRIX_UNITAIRE
            taux           = round((nb_convertis / nb_prospects) * 100, 1) if nb_prospects else 0
        except (ValueError, ZeroDivisionError):
            nb_convertis = nb_prospects = ca_encaisse = ca_pipeline = taux = 0

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            st.metric("💶 CA encaissé", f"{ca_encaisse:,} €".replace(",", " "), delta=f"{nb_convertis} client(s)")
        with pc2:
            st.metric("🎯 Taux de conversion", f"{taux} %", delta=f"{nb_convertis}/{nb_prospects}")
        with pc3:
            st.metric("📈 CA pipeline potentiel", f"{ca_pipeline:,} €".replace(",", " "), delta=f"{nb_prospects} prospects")
        with pc4:
            reste = nb_prospects - nb_convertis
            ca_reste = reste * PRIX_UNITAIRE
            st.metric("🔮 CA restant atteignable", f"{ca_reste:,} €".replace(",", " "), delta=f"{reste} à convertir")

        if nb_prospects > 0:
            progress_val = min(nb_convertis / nb_prospects, 1.0)
            st.progress(progress_val, text=f"Pipeline : {nb_convertis}/{nb_prospects} convertis ({taux}%)")

        st.divider()
        st.subheader("Répartition CRM par statut")
        prospects = get_crm_prospects(token)
        statuts_count = {}
        for p in prospects:
            s = extract_text(p.get("properties", {}).get("Statut", {}))
            if s:
                statuts_count[s] = statuts_count.get(s, 0) + 1

        if statuts_count:
            cols_s = st.columns(min(len(statuts_count), 6))
            for col, (statut, count) in zip(cols_s, sorted(statuts_count.items(), key=lambda x: -x[1])):
                with col:
                    st.metric(statut, count)
        else:
            st.info("Aucune donnée CRM disponible.")

# ─────────────────────────────────────────────
# PAGE 2 — CRM
# ─────────────────────────────────────────────
elif page == "📇 CRM Pipeline":
    st.title("📇 CRM Prospects")

    if not token:
        st.warning("Token Notion requis.")
    else:
        prospects = get_crm_prospects(token)
        if not prospects:
            st.info("Aucun prospect dans le CRM.")
        else:
            all_statuts = sorted({
                extract_text(p.get("properties", {}).get("Statut", {}))
                for p in prospects
            } - {""})
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtre = st.multiselect("Statut", all_statuts, default=all_statuts)
            with col_f2:
                search = st.text_input("🔍 Rechercher", placeholder="Cabinet, ville...")

            rows = []
            for p in prospects:
                props = p.get("properties", {})
                cabinet = extract_text(props.get("Cabinet", props.get("Name", props.get("Nom", {}))))
                contact = extract_text(props.get("Contact", props.get("Contact principal", {})))
                email   = extract_text(props.get("Email", {}))
                ville   = extract_text(props.get("Ville", {}))
                taille  = extract_text(props.get("Taille", {}))
                statut  = extract_text(props.get("Statut", {}))
                if statut not in filtre:
                    continue
                if search and search.lower() not in (cabinet + contact + ville).lower():
                    continue
                rows.append({"Cabinet": cabinet or "—", "Contact": contact or "—",
                             "Email": email or "—", "Ville": ville or "—",
                             "Taille": taille or "—", "Statut": statut or "—"})

            if rows:
                st.dataframe(rows, use_container_width=True, hide_index=True)
                st.caption(f"{len(rows)} prospect(s)")
            else:
                st.info("Aucun résultat.")

# ─────────────────────────────────────────────
# PAGE 3 — ROUTEUR
# ─────────────────────────────────────────────
elif page == "🤖 Envoyer instruction":
    st.title("🤖 Routeur SMD")
    st.caption("Tape une instruction en langage naturel — le Routeur la transmet au bon agent automatiquement")

    with st.expander("💡 Exemples d'instructions"):
        st.markdown("""
**Admin — Convertir :**  `Converti le cabinet Ficadex`

**Admin — Archiver :**  `Archive le cabinet Seleco, sans suite`

**Commercial :**  `Prospecte le cabinet ABC à Lyon, contact Jean Martin, email jean@abc.fr, TPE spécialisé audit`

**Marketing :**  `Crée un post LinkedIn sur les obligations RGPD pour les TPE, angle pratique, audience experts-comptables`
        """)

    instruction = st.text_area("Instruction", height=120, placeholder="Ex: Prospecte le cabinet Dupont Audit à Paris...")

    col1, col2 = st.columns([3, 1])
    with col1:
        send = st.button("🚀 Envoyer", type="primary", use_container_width=True, disabled=not instruction.strip())
    with col2:
        if st.button("🗑️ Effacer", use_container_width=True):
            st.rerun()

    if send and instruction.strip():
        with st.spinner("Envoi en cours..."):
            try:
                r = requests.post(
                    ROUTEUR_WEBHOOK,
                    json={"instruction": instruction.strip()},
                    timeout=20,
                )
                if r.status_code in (200, 201, 202, 204):
                    st.success("✅ Instruction envoyée ! Attends 10-15 secondes puis rafraîchis le CRM.")
                else:
                    st.error(f"❌ HTTP {r.status_code} : {r.text[:200]}")
            except requests.Timeout:
                st.warning("⏱️ Timeout — Make traite l'instruction en arrière-plan. Vérifie le CRM dans un instant.")
            except Exception as e:
                st.error(f"❌ {e}")

    st.divider()
    st.markdown("""
**Flux de traitement :**
```
Instruction → Routeur (Make) → Haiku → JSON structuré
    → smd-dispatcher (Supabase Edge Function)
        ├── admin/fiche_client  → Agent Admin Convertir
        ├── admin/archiver      → Agent Admin Archiver
        ├── commercial          → Agent Commercial (email + CRM)
        └── marketing           → Agent Marketing (LinkedIn + Notion)
```
    """)

# ─────────────────────────────────────────────
# PAGE 4 — MARKETING
# ─────────────────────────────────────────────
elif page == "📢 Marketing":
    st.title("📢 Contenus Marketing")

    if not token:
        st.warning("Token Notion requis.")
    else:
        contents = get_marketing_content(token)
        if not contents:
            st.info("Aucun contenu. Utilise l'onglet 'Envoyer instruction' avec une instruction Marketing.")
        else:
            st.caption(f"{len(contents)} contenu(s) généré(s)")
            for item in contents:
                props = item.get("properties", {})
                titre = ""
                for key in ("Sujet", "Titre", "Name", "title"):
                    t = extract_text(props.get(key, {}))
                    if t:
                        titre = t
                        break
                angle    = extract_text(props.get("Angle", {}))
                audience = extract_text(props.get("Audience", {}))
                created  = item.get("created_time", "")[:10]
                url      = item.get("url", "")
                with st.expander(f"📝 {titre or 'Sans titre'} — {created}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if angle:
                            st.markdown(f"**Angle :** {angle}")
                    with col2:
                        if audience:
                            st.markdown(f"**Audience :** {audience}")
                    if url:
                        st.markdown(f"[Ouvrir dans Notion ->]({url})")

# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# PAGE 5 — RAPPORT IA
# ─────────────────────────────────────────────
elif page == "🔬 Rapport IA":
    import json as _json

    TALLY_URL = "https://tally.so/r/rjpjW2"
    HAIKU_MODEL = "claude-haiku-4-5-20251001"

    QUESTIONS = {
        "Bloc A": [
            ("A1", "Registre des traitements de donnees", "CRITIQUE"),
            ("A2", "DPO ou referent RGPD nomme", "IMPORTANTE"),
            ("A3", "Employes formes au RGPD", "IMPORTANTE"),
        ],
        "Bloc B": [
            ("B1", "Politique de confidentialite sur le site", "CRITIQUE"),
            ("B2", "Bandeau cookies conforme", "CRITIQUE"),
            ("B3", "Case de consentement sur les formulaires web", "CRITIQUE"),
            ("B4", "Site securise HTTPS", "IMPORTANTE"),
        ],
        "Bloc C": [
            ("C1", "Sauvegardes regulieres des donnees", "CRITIQUE"),
            ("C2", "Mots de passe forts et uniques", "IMPORTANTE"),
            ("C3", "Antivirus et firewall actifs", "IMPORTANTE"),
            ("C4", "Plan de gestion des violations de donnees", "CRITIQUE"),
        ],
        "Bloc D": [
            ("D1", "DPA signes avec les prestataires", "CRITIQUE"),
            ("D2", "Prestataires dans l'UE ou pays adequats", "CRITIQUE"),
            ("D3", "Liste des sous-traitants tenue", "IMPORTANTE"),
        ],
        "Bloc E": [
            ("E1", "Reponse aux demandes d'acces en 30 jours", "CRITIQUE"),
            ("E2", "Suppression de donnees sur demande possible", "CRITIQUE"),
        ],
        "Bloc F": [
            ("F1", "Consentement explicite pour emails marketing", "CRITIQUE"),
            ("F2", "Lien de desinscription dans chaque email", "CRITIQUE"),
        ],
        "Bloc G": [
            ("G1", "Utilisation d'outils d'IA dans l'activite", "INFORMATIF"),
            ("G2", "Decisions automatiques sur des personnes par IA", "CRITIQUE"),
            ("G3", "Information clients interactions avec IA", "IMPORTANTE"),
            ("G4", "Evaluation des risques des outils d'IA", "CRITIQUE"),
        ],
    }

    BLOC_META = {
        "Bloc A": {"titre": "Registre des traitements", "max": 3},
        "Bloc B": {"titre": "Site web / Cookies", "max": 4},
        "Bloc C": {"titre": "Securite", "max": 4},
        "Bloc D": {"titre": "Sous-traitants", "max": 3},
        "Bloc E": {"titre": "Droits des personnes", "max": 2},
        "Bloc F": {"titre": "Email marketing", "max": 2},
        "Bloc G": {"titre": "EU AI Act", "max": 4},
    }

    # ────────────────────────────────────────
    st.title("🔬 Rapport IA — RGPD + AI Act")
    st.caption("Saisir les reponses Tally → analyse Claude → rapport PDF client")
    st.info("Questionnaire client : " + TALLY_URL)

    # 1. INFOS CLIENT
    st.subheader("1  Informations client")
    c1, c2 = st.columns(2)
    with c1:
        client_nom     = st.text_input("Nom entreprise *", placeholder="Cabinet Dupont")
        client_contact = st.text_input("Dirigeant", placeholder="Jean Dupont")
    with c2:
        client_email   = st.text_input("Email *", placeholder="jean@dupont.fr")
        client_secteur = st.text_input("Secteur", placeholder="Expertise comptable")
    client_salaries = st.text_input("Nb salaries", placeholder="12")

    # 2. REPONSES
    st.subheader("2  Reponses Tally")
    reponses = {}
    for bloc_k, questions in QUESTIONS.items():
        with st.expander(bloc_k + " — " + BLOC_META[bloc_k]["titre"], expanded=True):
            cols_q = st.columns(2)
            for idx, (code, label, niveau) in enumerate(questions):
                badge = "🔴" if niveau == "CRITIQUE" else ("🟠" if niveau == "IMPORTANTE" else "🔵")
                with cols_q[idx % 2]:
                    rep = st.radio(badge + " " + code + " — " + label, ["OUI", "NON"],
                                   index=None, key="rep_" + code, horizontal=True)
                    reponses[code] = rep

    # Score
    nb_rep   = sum(1 for v in reponses.values() if v is not None)
    score    = sum(1 for v in reponses.values() if v == "OUI")
    crit_non = [c for bk, qs in QUESTIONS.items()
                for (c, _, niv) in qs if niv == "CRITIQUE" and reponses.get(c) == "NON"]

    if nb_rep > 0:
        st.divider()
        if score >= 20:   niv_lbl, niv_col = "EXCELLENT", "green"
        elif score >= 14: niv_lbl, niv_col = "MOYEN", "orange"
        elif score >= 8:  niv_lbl, niv_col = "INSUFFISANT", "red"
        else:             niv_lbl, niv_col = "NON CONFORME", "red"

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Score global", str(score) + "/22")
        with m2: st.metric("Repondus", str(nb_rep) + "/22")
        with m3: st.metric("Niveau", niv_lbl)
        with m4:
            up = "150 EUR/mois" if score>=20 else ("1 500 EUR" if score>=14 else ("2 500 EUR" if score>=8 else "4 000 EUR"))
            st.metric("Upsell", up)

        if nb_rep >= 7:
            st.markdown("**Scores par bloc :**")
            bloc_cols = st.columns(7)
            for i, (bk, meta) in enumerate(BLOC_META.items()):
                sc_b = sum(1 for (c,_,__) in QUESTIONS[bk] if reponses.get(c) == "OUI")
                mx_b = meta["max"]
                with bloc_cols[i]:
                    col_m = "normal" if sc_b == mx_b else ("inverse" if sc_b < mx_b // 2 else "off")
                    st.metric(bk, str(sc_b) + "/" + str(mx_b), delta_color=col_m, delta="OK" if sc_b==mx_b else ("Lacunes" if sc_b>=mx_b//2 else "Critique"))

        if nb_rep == 22:
            st.progress(score / 22, text=str(score) + "/22 (" + str(round(score/22*100)) + "%)")
        if crit_non:
            st.error("Points CRITIQUE non conformes : " + ", ".join(crit_non))

    # 3. GENERATION IA
    st.divider()
    st.subheader("3  Analyse IA — Claude Haiku (rapide)")
    anthropic_key = get_anthropic_key()
    if not anthropic_key:
        st.warning("Cle API Anthropic manquante dans les Secrets Streamlit.")

    can_gen = bool(client_nom and anthropic_key and nb_rep >= 20)

    if st.button("Generer l'analyse IA", type="primary", disabled=not can_gen, use_container_width=True):
        # Construire le contexte compact
        rep_lines = []
        for bk, qs in QUESTIONS.items():
            for code, label, niveau in qs:
                rv = reponses.get(code) or "NR"
                rep_lines.append(code + ":" + rv + " [" + niveau[:4] + "] " + label)
        rep_compact = " | ".join(rep_lines)

        sc_str = str(score) + "/22"
        if score >= 20:   niv_str = "EXCELLENT"
        elif score >= 14: niv_str = "MOYEN"
        elif score >= 8:  niv_str = "INSUFFISANT"
        else:             niv_str = "NON CONFORME"

        bloc_scores = {}
        for bk, qs in QUESTIONS.items():
            sc_b = sum(1 for (c,_,__) in qs if reponses.get(c) == "OUI")
            bloc_scores[bk] = str(sc_b) + "/" + str(BLOC_META[bk]["max"])

        prompt_sys = "Tu es un expert RGPD et EU AI Act. Tu reponds UNIQUEMENT en JSON valide sans markdown."
        prompt_usr = (
            "Micro-audit RGPD+AI Act pour " + client_nom + " (" + (client_secteur or "secteur NC") +
            ", " + (client_salaries or "?") + " sal.). Score: " + sc_str + " — " + niv_str + "." +
            " Scores blocs: " + str(bloc_scores) + "." +
            " Reponses: " + rep_compact + "." +
            " Retourne ce JSON (CONCIS — max 50 mots par champ texte):" +
            """
{
  "synthese": "3 phrases : niveau, points forts, action urgente.",
  "risque_amende": "Montant max + article RGPD/AI Act applicable.",
  "blocs": [
    {"code": "A", "titre": "Registre", "score": 0, "max": 3,
     "statut": "CONFORME|PARTIEL|NON CONFORME",
     "lacune": "1 phrase si statut != CONFORME, sinon vide."}
  ],
  "recommandations": [
    {"priorite": "CRITIQUE", "code": "A1", "action": "Verbe + action specifique (20 mots max)",
     "delai": "0-30j", "article": "Art. XX RGPD"}
  ],
  "plan": [
    {"ordre": 1, "phase": "0-30j", "action": "Action courte",
     "responsable": "Dirigeant|Prestataire|Equipe IT",
     "cout": "Gratuit|< 100 EUR|> 500 EUR", "kpi": "Mesure courte"}
  ],
  "upsell": "1 phrase de proposition commerciale SMD adaptee au score."
}
Regles: blocs dans l'ordre A-G avec scores calcules; min 5 recommandations CRITIQUE en premier; plan couvre 0-30j, 30-90j, 90-180j; articles reels."""
        )

        with st.spinner("Claude Haiku analyse... (10-20 secondes)"):
            try:
                r = requests.post(
                    ANTHROPIC_API_URL,
                    headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": HAIKU_MODEL, "max_tokens": 4096,
                          "system": prompt_sys,
                          "messages": [{"role": "user", "content": prompt_usr}]},
                    timeout=60,
                )
                if r.status_code != 200:
                    st.error("Erreur API HTTP " + str(r.status_code) + " : " + r.text[:300])
                else:
                    raw = r.json()["content"][0]["text"].strip()
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"): raw = raw[4:]
                    data = _json.loads(raw)
                    st.session_state["ia"] = {"data": data, "nom": client_nom,
                        "email": client_email, "contact": client_contact,
                        "secteur": client_secteur, "salaries": client_salaries,
                        "score": score, "niveau": niv_str, "reponses": dict(reponses),
                        "bloc_scores": bloc_scores}
                    st.success("Analyse generee !")
                    st.rerun()
            except _json.JSONDecodeError as e:
                st.error("JSON invalide : " + str(e))
                st.code(raw[:600])
            except Exception as e:
                st.error("Erreur : " + str(e))

    if not can_gen:
        miss = []
        if not client_nom:    miss.append("nom entreprise")
        if not anthropic_key: miss.append("cle API")
        if nb_rep < 20:       miss.append(str(20-nb_rep) + " reponses manquantes")
        if miss: st.caption("Manquant : " + " | ".join(miss))

    # ── AFFICHAGE RESULTATS ────────────────────────────────────
    if "ia" in st.session_state:
        s      = st.session_state["ia"]
        data   = s["data"]
        nom    = s["nom"]
        sc     = s["score"]
        nv     = s["niveau"]
        blocs  = data.get("blocs", [])
        recos  = data.get("recommandations", [])
        plan   = data.get("plan", [])

        st.divider()
        st.subheader("Rapport — " + nom + " — " + str(sc) + "/22 — " + nv)

        # KPIs globaux
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: st.metric("Score", str(sc) + "/22")
        with k2: st.metric("Niveau", nv)
        with k3:
            n_crit = sum(1 for r in recos if r.get("priorite") == "CRITIQUE")
            st.metric("Points CRITIQUE", str(n_crit))
        with k4:
            n_ok = sum(1 for b in blocs if b.get("statut") == "CONFORME")
            st.metric("Blocs conformes", str(n_ok) + "/7")
        with k5:
            up_m = "150 EUR/mois" if sc>=20 else ("1 500 EUR" if sc>=14 else ("2 500 EUR" if sc>=8 else "4 000 EUR"))
            st.metric("Mission upsell", up_m)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Synthese", "Blocs", "Recommandations", "Plan d'action", "PDF client"])

        with tab1:
            st.info(data.get("synthese", ""))
            st.error("Risque amende : " + data.get("risque_amende", ""))

        with tab2:
            rows_b = []
            for b in blocs:
                statut = b.get("statut", "")
                rows_b.append({
                    "Bloc": b.get("code", ""), "Theme": b.get("titre", ""),
                    "Score": str(b.get("score", "")) + "/" + str(b.get("max", "")),
                    "Statut": statut, "Lacune principale": b.get("lacune", "")
                })
            st.dataframe(rows_b, use_container_width=True, hide_index=True,
                column_config={
                    "Statut": st.column_config.TextColumn(width="medium"),
                    "Lacune principale": st.column_config.TextColumn(width="large"),
                })

        with tab3:
            rows_r = []
            for r in recos:
                rows_r.append({
                    "Priorite": r.get("priorite", ""), "Code": r.get("code", ""),
                    "Action": r.get("action", ""), "Delai": r.get("delai", ""),
                    "Article": r.get("article", "")
                })
            st.dataframe(rows_r, use_container_width=True, hide_index=True,
                column_config={
                    "Priorite": st.column_config.TextColumn(width="small"),
                    "Code": st.column_config.TextColumn(width="small"),
                    "Action": st.column_config.TextColumn(width="large"),
                })

        with tab4:
            rows_p = []
            for p in plan:
                rows_p.append({
                    "#": p.get("ordre", ""), "Phase": p.get("phase", ""),
                    "Action": p.get("action", ""), "Responsable": p.get("responsable", ""),
                    "Cout": p.get("cout", ""), "KPI": p.get("kpi", "")
                })
            st.dataframe(rows_p, use_container_width=True, hide_index=True)

        with tab5:
            st.markdown("**Rapport PDF a remettre au client**")
            st.caption(data.get("upsell", ""))

            from datetime import date as _date

            # Generation HTML rapport client
            def statut_color(st_val):
                return "#1B7C3D" if st_val == "CONFORME" else ("#C45A00" if st_val == "PARTIEL" else "#B00020")

            def prio_color(p):
                return "#B00020" if p == "CRITIQUE" else ("#C45A00" if p == "IMPORTANTE" else "#1A2B5E")

            blocs_html = ""
            for b in blocs:
                sc_b = b.get("score", 0); mx_b = b.get("max", 1)
                pct = round(sc_b / mx_b * 100) if mx_b else 0
                st_v = b.get("statut", "")
                lacune = b.get("lacune", "")
                blocs_html += (
                    "<tr>"
                    "<td style='font-weight:bold'>" + b.get("code","") + " — " + b.get("titre","") + "</td>"
                    "<td style='text-align:center'>" + str(sc_b) + "/" + str(mx_b) + "</td>"
                    "<td><div style='background:#eee;border-radius:4px;height:12px'>"
                    "<div style='background:" + statut_color(st_v) + ";width:" + str(pct) + "%;height:12px;border-radius:4px'></div></div></td>"
                    "<td style='color:" + statut_color(st_v) + ";font-weight:bold'>" + st_v + "</td>"
                    "<td style='font-size:11px;color:#555'>" + lacune + "</td>"
                    "</tr>"
                )

            recos_html = ""
            for rc in recos:
                recos_html += (
                    "<tr>"
                    "<td style='color:" + prio_color(rc.get("priorite","")) + ";font-weight:bold;font-size:11px'>" + rc.get("priorite","") + "</td>"
                    "<td style='font-weight:bold;color:#1A2B5E'>" + rc.get("code","") + "</td>"
                    "<td>" + rc.get("action","") + "</td>"
                    "<td style='font-size:11px'>" + rc.get("delai","") + "</td>"
                    "<td style='font-size:10px;color:#666'>" + rc.get("article","") + "</td>"
                    "</tr>"
                )

            plan_html = ""
            for pl in plan:
                plan_html += (
                    "<tr>"
                    "<td style='font-weight:bold;color:#1A2B5E'>" + pl.get("phase","") + "</td>"
                    "<td>" + pl.get("action","") + "</td>"
                    "<td>" + pl.get("responsable","") + "</td>"
                    "<td style='font-size:11px'>" + pl.get("cout","") + "</td>"
                    "<td style='font-size:11px;color:#555'>" + pl.get("kpi","") + "</td>"
                    "</tr>"
                )

            if sc >= 20: niv_color, niv_bg = "#1B7C3D", "#E8F5EE"
            elif sc >= 14: niv_color, niv_bg = "#C45A00", "#FFF3E8"
            elif sc >= 8: niv_color, niv_bg = "#B00020", "#FFE8EB"
            else: niv_color, niv_bg = "#B00020", "#FFE8EB"

            html_report = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<title>Micro-audit RGPD + AI Act — """ + nom + """</title>
<style>
  body{font-family:Arial,sans-serif;margin:0;padding:0;color:#222;font-size:12px}
  .header{background:#1A2B5E;color:white;padding:24px 32px;display:flex;justify-content:space-between;align-items:center}
  .header h1{margin:0;font-size:18px;font-weight:bold}
  .header .sub{font-size:11px;opacity:.8;margin-top:4px}
  .cover{padding:32px;background:#f8f9fc;border-bottom:3px solid #C9A84C}
  .score-box{display:inline-block;background:""" + niv_bg + """;border:2px solid """ + niv_color + """;border-radius:8px;padding:16px 32px;text-align:center;margin:16px 0}
  .score-num{font-size:48px;font-weight:bold;color:""" + niv_color + """;line-height:1}
  .score-lbl{font-size:14px;color:""" + niv_color + """;font-weight:bold;margin-top:4px}
  .client-info{margin:16px 0;display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .info-item{background:white;padding:8px 12px;border-radius:4px;border-left:3px solid #1A2B5E}
  .info-label{font-size:10px;color:#666;text-transform:uppercase}
  .info-val{font-weight:bold;margin-top:2px}
  .synthese{background:white;border-left:4px solid #1A2B5E;padding:12px 16px;margin:16px 0;border-radius:0 4px 4px 0}
  .amende-box{background:#FFE8EB;border-left:4px solid #B00020;padding:10px 16px;margin:8px 0;border-radius:0 4px 4px 0;font-size:11px}
  section{padding:20px 32px;border-bottom:1px solid #eee}
  h2{color:#1A2B5E;font-size:14px;border-bottom:2px solid #C9A84C;padding-bottom:4px;margin-bottom:12px}
  table{width:100%;border-collapse:collapse;font-size:11px}
  th{background:#1A2B5E;color:white;padding:6px 10px;text-align:left;font-size:10px;text-transform:uppercase}
  td{padding:6px 10px;border-bottom:1px solid #eee}
  tr:nth-child(even) td{background:#f9f9f9}
  .footer{background:#1A2B5E;color:white;padding:12px 32px;font-size:10px;display:flex;justify-content:space-between}
  .upsell{background:#FDF8EE;border:2px solid #C9A84C;border-radius:6px;padding:14px 20px;margin:12px 0}
  @media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
</style></head><body>

<div class="header">
  <div>
    <div class="header h1">SMD GLOBAL CONSULTING LLC</div>
    <div class="sub">Rapport Micro-audit RGPD + AI Act — Confidentiel</div>
  </div>
  <div style="text-align:right;font-size:11px">""" + _date.today().strftime("%d/%m/%Y") + """<br>Ref. SMD-""" + _date.today().strftime("%Y%m%d") + "-" + nom[:3].upper() + """</div>
</div>

<div class="cover">
  <div class="score-box">
    <div class="score-num">""" + str(sc) + """/22</div>
    <div class="score-lbl">""" + nv + """</div>
  </div>
  <div class="client-info">
    <div class="info-item"><div class="info-label">Entreprise</div><div class="info-val">""" + nom + """</div></div>
    <div class="info-item"><div class="info-label">Secteur</div><div class="info-val">""" + (s.get("secteur") or "—") + """</div></div>
    <div class="info-item"><div class="info-label">Dirigeant</div><div class="info-val">""" + (s.get("contact") or "—") + """</div></div>
    <div class="info-item"><div class="info-label">Effectif</div><div class="info-val">""" + (s.get("salaries") or "—") + """ salaries</div></div>
  </div>
  <div class="synthese">""" + data.get("synthese", "") + """</div>
  <div class="amende-box"><strong>Risque d'amende :</strong> """ + data.get("risque_amende", "") + """</div>
</div>

<section>
<h2>Tableau de bord par bloc</h2>
<table>
<thead><tr><th>Bloc</th><th>Score</th><th style="width:120px">Avancement</th><th>Statut</th><th>Lacune principale</th></tr></thead>
<tbody>""" + blocs_html + """</tbody>
</table>
</section>

<section>
<h2>Recommandations prioritaires</h2>
<table>
<thead><tr><th>Priorite</th><th>Ref.</th><th>Action a mener</th><th>Delai</th><th>Reference legale</th></tr></thead>
<tbody>""" + recos_html + """</tbody>
</table>
</section>

<section>
<h2>Plan d'action</h2>
<table>
<thead><tr><th>Phase</th><th>Action</th><th>Responsable</th><th>Cout</th><th>KPI de suivi</th></tr></thead>
<tbody>""" + plan_html + """</tbody>
</table>
</section>

<section>
<h2>Pour aller plus loin</h2>
<div class="upsell">""" + data.get("upsell", "") + """</div>
<p style="font-size:11px;color:#555">SMD Global Consulting LLC accompagne les entreprises dans leur mise en conformite RGPD et EU AI Act.
Contact : diallosouleymane19@gmail.com</p>
</section>

<div class="footer">
  <span>SMD Global Consulting LLC — diallosouleymane19@gmail.com</span>
  <span>Rapport genere le """ + _date.today().strftime("%d/%m/%Y") + """ — Confidentiel</span>
</div>
</body></html>"""

            fname = "Rapport_RGPD_AIAct_" + nom.replace(" ", "_") + "_" + _date.today().strftime("%Y%m%d") + ".html"
            st.download_button(
                label="Telecharger le rapport PDF (HTML → imprimer en PDF)",
                data=html_report.encode("utf-8"),
                file_name=fname,
                mime="text/html",
                use_container_width=True,
                type="primary",
            )
            st.caption("Ouvrir le fichier HTML → Ctrl+P (ou Cmd+P) → Enregistrer en PDF → remettre au client.")

        st.divider()
        if st.button("Effacer et nouveau client", type="secondary"):
            st.session_state.pop("ia", None)
            st.rerun()

# PAGE 6 — SYSTEME
# ─────────────────────────────────────────────
elif page == "⚙️ Système":
    st.title("État du système")

    scenarios = {
        "Routeur SMD":             {"id": 6258440, "hook": "...5hbyls7..."},
        "Admin Convertir":         {"id": 6259845, "hook": "...kimneh2j..."},
        "Admin Archiver":          {"id": 6259927, "hook": "...buy5qft5..."},
        "Agent Commercial":        {"id": 6245020, "hook": "...7lgy38z..."},
        "Agent Marketing":         {"id": 6245203, "hook": "...ypu71qq..."},
        "Alertes Erreurs":         {"id": 6260014, "hook": "...y1c2qms5..."},
        "Dashboard KPIs update":   {"id": 6260071, "hook": "daily 08:00"},
        "Agent Pilote Paiement":   {"id": 6266361, "hook": "...9m3mu4i5... (Stripe)"},
    }

    make_key = get_make_api_key()
    if not make_key:
        st.info("Ajoute make.api_key dans les secrets pour voir le statut en temps reel.")

    for name, info in scenarios.items():
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.markdown("**" + name + "** — `#" + str(info["id"]) + "`")
        with col2:
            if make_key:
                try:
                    r = requests.get(
                        "https://eu1.make.com/api/v2/scenarios/" + str(info["id"]),
                        headers={"Authorization": "Token " + make_key},
                        timeout=5,
                    )
                    if r.status_code == 200:
                        active = r.json().get("scenario", {}).get("isActive", False)
                        st.markdown("Actif" if active else "Inactif")
                    else:
                        st.markdown("?")
                except Exception:
                    st.markdown("?")
            else:
                st.markdown("-")
        with col3:
            st.caption(info["hook"])

    st.divider()
    st.subheader("Test rapide")
    if st.button("Ping Routeur SMD"):
        with st.spinner("Test en cours..."):
            try:
                r = requests.post(ROUTEUR_WEBHOOK, json={"instruction": "test ping"}, timeout=10)
                if r.status_code in (200, 201, 202, 204):
                    st.success("Webhook operationnel HTTP " + str(r.status_code))
                else:
                    st.error("HTTP " + str(r.status_code))
            except Exception as e:
                st.error(str(e))

