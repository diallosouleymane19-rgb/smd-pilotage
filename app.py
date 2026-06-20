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
ROUTEUR_WEBHOOK = "https://hook.eu1.make.com/5hbyls7ztgpvc76avtx06h3gfpbi4u2o"

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
        ["📊 KPIs", "📇 CRM Pipeline", "🤖 Envoyer instruction", "📢 Marketing", "⚙️ Système"],
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
# PAGE 5 — SYSTÈME
# ─────────────────────────────────────────────
elif page == "⚙️ Système":
    st.title("⚙️ État du système")

    scenarios = {
        "🔀 Routeur SMD":             {"id": 6258440, "hook": "...5hbyls7..."},
        "🏢 Admin Convertir":          {"id": 6259845, "hook": "...kimneh2j..."},
        "📁 Admin Archiver":           {"id": 6259927, "hook": "...buy5qft5..."},
        "📧 Agent Commercial":         {"id": 6245020, "hook": "...7lgy38z..."},
        "📢 Agent Marketing":          {"id": 6245203, "hook": "...ypu71qq..."},
        "🔔 Alertes Erreurs":          {"id": 6260014, "hook": "...y1c2qms5..."},
        "📊 Dashboard KPIs update":    {"id": 6260071, "hook": "daily 08:00"},
        "💳 Agent Pilote — Paiement":  {"id": 6266361, "hook": "...9m3mu4i5... (Stripe)"},
    }

    make_key = get_make_api_key()
    if not make_key:
        st.info("Ajoute `make.api_key` dans les secrets pour voir le statut en temps réel.")

    for name, info in scenarios.items():
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.markdown(f"**{name}** — `#{info['id']}`")
        with col2:
            if make_key:
                try:
                    r = requests.get(
                        f"https://eu1.make.com/api/v2/scenarios/{info['id']}",
                        headers={"Authorization": f"Token {make_key}"},
                        timeout=5,
                    )
                    if r.status_code == 200:
                        active = r.json().get("scenario", {}).get("isActive", False)
                        st.markdown("🟢 Actif" if active else "🔴 Inactif")
                    else:
                        st.markdown("❓")
                except Exception:
                    st.markdown("❓")
            else:
                st.markdown("⚪")
        with col3:
            st.caption(info["hook"])

    st.divider()
    st.subheader("Test rapide")
    if st.button("🧪 Ping Routeur SMD"):
        with st.spinner("Test en cours..."):
            try:
                r = requests.post(ROUTEUR_WEBHOOK, json={"instruction": "test ping"}, timeout=10)
                if r.status_code in (200, 201, 202, 204):
                    st.success(f"✅ Webhook opérationnel (HTTP {r.status_code})")
                else:
                    st.error(f"❌ HTTP {r.status_code}")
            except Exception as e:
                st.error(f"❌ {e}")
