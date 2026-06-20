# Dashboard Pilotage SMD

Interface centralisée pour piloter le système Agent Pilotage SMD (Make + Notion + Supabase).

## Fonctionnalités
- **KPIs** — 4 indicateurs clés mis à jour automatiquement chaque matin
- **CRM Pipeline** — Vue et filtrage des prospects Notion
- **Routeur SMD** — Envoyer une instruction en langage naturel aux agents
- **Marketing** — Aperçu des contenus LinkedIn générés
- **Système** — État des scénarios Make, test du webhook

## Déploiement sur Streamlit Cloud

### 1. Préparer GitHub
```bash
git init
git add app.py requirements.txt .gitignore
git commit -m "Initial SMD Dashboard"
# Créer un repo sur GitHub et pousser
git remote add origin https://github.com/TON_COMPTE/smd-dashboard.git
git push -u origin main
```

### 2. Déployer sur Streamlit Cloud
1. Aller sur https://share.streamlit.io
2. "New app" → sélectionner ton repo GitHub → `app.py`
3. Dans "Advanced settings" → "Secrets" → coller :

```toml
[notion]
token = "secret_VOTRE_TOKEN_NOTION"

[make]
api_key = "VOTRE_MAKE_API_KEY"
```

### 3. Obtenir le token Notion
1. Aller sur https://www.notion.so/my-integrations
2. Cliquer "New integration"
3. Nom : "SMD Dashboard Streamlit"
4. Capabilities : Read content (minimum)
5. Copier le "Internal Integration Token" (commence par `secret_`)
6. Partager chaque DB Notion avec cette intégration :
   - DB CRM → `...` → Connexions → SMD Dashboard Streamlit
   - DB Dashboard → idem
   - DB Marketing → idem

### 4. Obtenir la Make API Key
1. Dans Make → ton profil → API
2. "Generate new token"
3. Copier la clé

## Structure
```
smd_dashboard/
├── app.py              # Application principale
├── requirements.txt    # Dépendances Python
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml    # Secrets locaux (NE PAS committer)
```
