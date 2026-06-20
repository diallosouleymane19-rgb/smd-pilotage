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
# PAGE 5 — RAPPORT IA

elif page == "🔬 Rapport IA":
    import json as _json

    st.title("🔬 Generateur de rapport IA")
    st.caption("Saisir les reponses Tally -> Claude analyse -> rapport structure pret a envoyer au client")

    TALLY_URL = "https://tally.so/r/68VQyB"
    st.info("Lien questionnaire client : " + TALLY_URL)

    QUESTIONS = {
        "Bloc A — Registre des traitements": [
            ("A1", "Avez-vous un registre des traitements de donnees ?", "CRITIQUE"),
            ("A2", "Avez-vous nomme un DPO ou referent RGPD ?", "IMPORTANTE"),
            ("A3", "Vos employes sont-ils formes au RGPD ?", "IMPORTANTE"),
        ],
        "Bloc B — Site web / Cookies": [
            ("B1", "Avez-vous une politique de confidentialite sur votre site ?", "CRITIQUE"),
            ("B2", "Avez-vous un bandeau cookies conforme ?", "CRITIQUE"),
            ("B3", "Vos formulaires web ont-ils une case de consentement ?", "CRITIQUE"),
            ("B4", "Votre site est-il securise en HTTPS ?", "IMPORTANTE"),
        ],
        "Bloc C — Securite": [
            ("C1", "Vos donnees sont-elles sauvegardees regulierement ?", "CRITIQUE"),
            ("C2", "Utilisez-vous des mots de passe forts et uniques ?", "IMPORTANTE"),
            ("C3", "Avez-vous un antivirus/firewall actif ?", "IMPORTANTE"),
            ("C4", "Avez-vous un plan en cas de violation de donnees ?", "CRITIQUE"),
        ],
        "Bloc D — Sous-traitants": [
            ("D1", "Avez-vous signe des DPA avec vos prestataires ?", "CRITIQUE"),
            ("D2", "Vos prestataires sont-ils tous dans l'UE ou pays adequats ?", "CRITIQUE"),
            ("D3", "Avez-vous une liste de vos sous-traitants ?", "IMPORTANTE"),
        ],
        "Bloc E — Droits des personnes": [
            ("E1", "Pouvez-vous repondre a une demande d'acces aux donnees en 30 jours ?", "CRITIQUE"),
            ("E2", "Pouvez-vous supprimer les donnees d'une personne sur demande ?", "CRITIQUE"),
        ],
        "Bloc F — Email marketing": [
            ("F1", "Avez-vous le consentement explicite pour vos emails marketing ?", "CRITIQUE"),
            ("F2", "Proposez-vous un lien de desinscription dans chaque email ?", "CRITIQUE"),
        ],
        "Bloc G — EU AI Act": [
            ("G1", "Utilisez-vous des outils d'IA dans votre activite ?", "INFORMATIF"),
            ("G2", "Ces outils d'IA prennent-ils des decisions automatiques sur des personnes ?", "CRITIQUE"),
            ("G3", "Informez-vous vos clients quand ils interagissent avec une IA ?", "IMPORTANTE"),
            ("G4", "Avez-vous evalue les risques de vos outils d'IA ?", "CRITIQUE"),
        ],
    }

    # ── 1. Informations client ────────────────────────────────
    st.subheader("1  Informations client")
    c1, c2 = st.columns(2)
    with c1:
        client_nom     = st.text_input("Nom de l'entreprise *", placeholder="Cabinet Dupont")
        client_contact = st.text_input("Nom du dirigeant", placeholder="Jean Dupont")
    with c2:
        client_email   = st.text_input("Email client *", placeholder="jean@dupont.fr")
        client_secteur = st.text_input("Secteur", placeholder="Expertise comptable")
    client_salaries = st.text_input("Nombre de salaries", placeholder="12")

    # ── 2. Reponses Tally ─────────────────────────────────────
    st.subheader("2  Reponses du questionnaire Tally")
    st.caption("Saisir les reponses recues dans Tally > Submissions")

    reponses = {}
    for bloc_titre, questions in QUESTIONS.items():
        with st.expander(bloc_titre, expanded=True):
            cols_q = st.columns(2)
            for idx, (code, question, niveau) in enumerate(questions):
                badge = "CRITIQUE" if niveau == "CRITIQUE" else ("IMPORT." if niveau == "IMPORTANTE" else "INFO")
                with cols_q[idx % 2]:
                    rep = st.radio(
                        f"[{badge}] {code} — {question}",
                        ["OUI", "NON"],
                        index=None,
                        key="rep_" + code,
                        horizontal=True,
                    )
                    reponses[code] = rep

    # ── Score en temps reel ───────────────────────────────────
    nb_rep   = sum(1 for v in reponses.values() if v is not None)
    score    = sum(1 for v in reponses.values() if v == "OUI")
    crit_non = [c for bl, qs in QUESTIONS.items()
                for (c, _, niv) in qs if niv == "CRITIQUE" and reponses.get(c) == "NON"]

    if nb_rep > 0:
        st.divider()
        st.subheader("Score en temps reel")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Score", str(score) + " / 22")
        with m2:
            st.metric("Repondus", str(nb_rep) + " / 22")
        with m3:
            if score >= 20:   niv_lbl = "EXCELLENT"
            elif score >= 14: niv_lbl = "MOYEN"
            elif score >= 8:  niv_lbl = "INSUFFISANT"
            else:             niv_lbl = "NON CONFORME"
            st.metric("Niveau", niv_lbl)
        with m4:
            if score >= 20:   up_prix = "150 EUR/mois"
            elif score >= 14: up_prix = "1 500 EUR"
            elif score >= 8:  up_prix = "2 500 EUR"
            else:             up_prix = "4 000 EUR"
            st.metric("Upsell", up_prix)
        if nb_rep == 22:
            st.progress(score / 22, text=str(score) + "/22 (" + str(round(score / 22 * 100)) + "%)")
        if crit_non:
            st.error("Points CRITIQUE non conformes : " + ", ".join(crit_non))

    # ── 3. Generation IA ─────────────────────────────────────
    st.divider()
    st.subheader("3  Analyse IA — Claude Sonnet")

    anthropic_key = get_anthropic_key()
    if not anthropic_key:
        st.warning("Cle API Anthropic manquante. Ajouter dans Streamlit Cloud > Secrets :\n[anthropic]\napi_key = \"sk-ant-...\"")

    can_gen = bool(client_nom and anthropic_key and nb_rep >= 20)

    if st.button("Generer l'analyse IA", type="primary", disabled=not can_gen, use_container_width=True):
        lignes = []
        for bt, qs in QUESTIONS.items():
            lignes.append("\n--- " + bt + " ---")
            for code, question, niveau in qs:
                rv = reponses.get(code) or "Non repondu"
                lignes.append("[" + code + "] (" + niveau + ") " + question + " : " + rv)
        rep_txt = "\n".join(lignes)

        if score >= 20:   niv_str = "EXCELLENT"
        elif score >= 14: niv_str = "MOYEN"
        elif score >= 8:  niv_str = "INSUFFISANT"
        else:             niv_str = "NON CONFORME"

        sys_prompt = (
            "Tu es un expert en conformite RGPD et EU AI Act. "
            "Tu analyses des questionnaires d'audit pour SMD Global Consulting LLC. "
            "Tu reponds UNIQUEMENT en JSON valide, sans texte avant ni apres."
        )

        user_prompt = (
            "Analyse ce micro-audit RGPD + AI Act.\n\n"
            "CLIENT :\n"
            "- Entreprise : " + client_nom + "\n"
            "- Dirigeant : " + (client_contact or "Non renseigne") + "\n"
            "- Secteur : " + (client_secteur or "Non renseigne") + "\n"
            "- Salaries : " + (client_salaries or "Non renseigne") + "\n\n"
            "SCORE : " + str(score) + "/22 — Niveau : " + niv_str + "\n\n"
            "REPONSES :\n" + rep_txt + "\n\n"
            "Genere ce JSON :\n"
            "{\n"
            '  "synthese_executive": "Paragraphe 100 mots : niveau conformite, risques, action prioritaire.",\n'
            '  "risque_amende": "Risque amende CNIL/AI Act : montants reels, articles. 2-3 phrases.",\n'
            '  "analyse_blocs": {\n'
            '    "A": {"score": 0, "max": 3, "titre": "Registre des traitements", "analyse": "2-3 phrases."},\n'
            '    "B": {"score": 0, "max": 4, "titre": "Site web / Cookies", "analyse": "2-3 phrases."},\n'
            '    "C": {"score": 0, "max": 4, "titre": "Securite", "analyse": "2-3 phrases."},\n'
            '    "D": {"score": 0, "max": 3, "titre": "Sous-traitants", "analyse": "2-3 phrases."},\n'
            '    "E": {"score": 0, "max": 2, "titre": "Droits des personnes", "analyse": "2-3 phrases."},\n'
            '    "F": {"score": 0, "max": 2, "titre": "Email marketing", "analyse": "2-3 phrases."},\n'
            '    "G": {"score": 0, "max": 4, "titre": "EU AI Act", "analyse": "2-3 phrases."}\n'
            "  },\n"
            '  "recommandations": [\n'
            '    {"priorite": "CRITIQUE", "code_question": "A1", "action": "Action concrete.", "pourquoi": "Risque legal.", "delai": "0-30 jours", "article": "Art. 30 RGPD"}\n'
            "  ],\n"
            '  "plan_action": [\n'
            '    {"ordre": 1, "action": "Action", "responsable": "Qui", "delai": "0-30j", "ressource": "Outil", "kpi": "Mesure"}\n'
            "  ],\n"
            '  "opportunite_commerciale": "Proposition mission SMD adaptee au score."\n'
            "}\n\n"
            "Regles : scores calcules d'apres les OUI, min 5 recommandations CRITIQUE en premier, "
            "plan couvrant 0-30j/30-90j/90-180j, articles de loi reels."
        )

        with st.spinner("Claude Sonnet analyse... (30-60 secondes)"):
            try:
                r = requests.post(
                    ANTHROPIC_API_URL,
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": ANTHROPIC_MODEL,
                        "max_tokens": 8192,
                        "system": sys_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                    timeout=90,
                )
                if r.status_code != 200:
                    st.error("Erreur API HTTP " + str(r.status_code) + " : " + r.text[:300])
                else:
                    raw = r.json()["content"][0]["text"].strip()
                    if raw.startswith("```"):
                        parts = raw.split("```")
                        raw = parts[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    st.session_state["ia_result"]  = _json.loads(raw)
                    st.session_state["ia_nom"]     = client_nom
                    st.session_state["ia_score"]   = score
                    st.session_state["ia_niveau"]  = niv_str
                    st.success("Analyse generee avec succes !")
                    st.rerun()
            except _json.JSONDecodeError as e:
                st.error("JSON invalide : " + str(e))
                st.code(raw[:500])
            except Exception as e:
                st.error("Erreur : " + str(e))

    if not can_gen:
        missing = []
        if not client_nom:     missing.append("nom de l'entreprise")
        if not anthropic_key:  missing.append("cle API Anthropic")
        if nb_rep < 20:        missing.append(str(20 - nb_rep) + " reponses manquantes")
        if missing:
            st.caption("Manquant : " + " | ".join(missing))

    # ── Affichage resultats ───────────────────────────────────
    if "ia_result" in st.session_state:
        res = st.session_state["ia_result"]
        nom = st.session_state.get("ia_nom", client_nom)
        sc  = st.session_state.get("ia_score", score)
        nv  = st.session_state.get("ia_niveau", "")

        st.divider()
        st.subheader("Analyse — " + nom + " — " + str(sc) + "/22 — " + nv)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Synthese", "Par bloc", "Recommandations", "Plan d'action", "Commercial"]
        )

        with tab1:
            st.markdown("**Synthese executive**")
            st.text_area("Copier dans le rapport Word", value=res.get("synthese_executive", ""),
                         height=180, key="edit_synthese")
            st.markdown("**Risque amende estime**")
            st.text_area(" ", value=res.get("risque_amende", ""), height=110, key="edit_amende")

        with tab2:
            for lettre, data in res.get("analyse_blocs", {}).items():
                sb  = data.get("score", 0)
                mb  = data.get("max", 1)
                tb  = data.get("titre", "Bloc " + lettre)
                pct = sb / mb if mb else 0
                col = "green" if pct == 1.0 else ("orange" if pct >= 0.5 else "red")
                st.markdown("**Bloc " + lettre + " — " + tb + "** : :" + col + "[" + str(sb) + "/" + str(mb) + "]")
                st.text_area("analyse_" + lettre, value=data.get("analyse", ""),
                             height=90, key="edit_b_" + lettre, label_visibility="collapsed")

        with tab3:
            for i, reco in enumerate(res.get("recommandations", []), 1):
                prio  = reco.get("priorite", "")
                col   = "red" if prio == "CRITIQUE" else ("orange" if prio == "IMPORTANTE" else "blue")
                st.markdown(str(i) + ". :" + col + "[" + prio + "]" + " `" + reco.get("code_question", "") + "` — " + reco.get("action", ""))
                ca, cb = st.columns(2)
                with ca:
                    st.caption("Pourquoi : " + reco.get("pourquoi", ""))
                with cb:
                    st.caption("Delai : " + reco.get("delai", "") + "  |  " + reco.get("article", ""))
                st.markdown("---")

        with tab4:
            plan = res.get("plan_action", [])
            if plan:
                st.dataframe(
                    [{"#": p.get("ordre", ""), "Action": p.get("action", ""),
                      "Responsable": p.get("responsable", ""), "Delai": p.get("delai", ""),
                      "Ressource": p.get("ressource", ""), "KPI": p.get("kpi", "")}
                     for p in plan],
                    use_container_width=True, hide_index=True,
                )

        with tab5:
            st.success("Proposition commerciale generee par l'IA")
            st.text_area("A inclure dans l'email de livraison",
                         value=res.get("opportunite_commerciale", ""), height=180, key="edit_comm")
            if sc >= 20:
                st.info("Proposer : Veille reglementaire — 150 EUR/mois")
            elif sc >= 14:
                st.warning("Proposer : Mission conformite complete — 1 500 EUR")
            elif sc >= 8:
                st.error("Proposer : Mission urgente 6 mois — 2 500 EUR")
            else:
                st.error("Proposer : Mission complete + DPO externalise — 4 000 EUR")

        st.divider()
        if st.button("Effacer et recommencer", type="secondary"):
            for k in ["ia_result", "ia_nom", "ia_score", "ia_niveau"]:
                st.session_state.pop(k, None)
            st.rerun()


# ─────────────────────────────────────────────
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
