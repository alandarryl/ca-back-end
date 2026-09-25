
# CompanyAudit — Backend API

Backend FastAPI pour l'application **CompanyAudit**, une solution full-stack permettant de générer automatiquement des fiches d'audit d'entreprises structurées pour la préparation d'entretiens d'embauche, de candidatures ou d'analyses B2B.

L'application prend en charge la recherche web automatique, la structuration par intelligence artificielle (support **hybride local/cloud**) et l'export dynamique au format PDF.

---

## Stack Technique

* **FastAPI** — Framework web Python asynchrone hautement performant.
* **Pydantic v2** — Validation stricte des données et génération de schémas JSON.
* **Ollama** — Moteur d'inférence LLM local pour exécuter des modèles légers (ex: `qwen2.5:1.5b`, `phi3:mini`) en illimité et hors-ligne.
* **Google GenAI SDK** — Intégration de l'API Gemini (`gemini-2.5-flash`, `gemini-3.8-flash`) pour des analyses rapides dans le cloud.
* **ReportLab** — Génération dynamique de documents PDF professionnels en mémoire (`BytesIO`).
* **DuckDuckGo Search (`ddgs`)** — Scraping/recherche web sans clé d'API requis.
* **Uvicorn** — Serveur ASGI léger pour le développement et la production.

---

## Architecture du Projet

```text
company-audit-back/
│
├── schemas/
│   └── audit_schema.py   → Schémas Pydantic (CompanyAuditSchema) garantissant le format JSON
│
├── services/
│   ├── ai_service.py     → Moteur IA multi-provider (Ollama / Gemini) avec mode sectionné & cache
│   ├── pdf_service.py    → Générateur de rapports PDF personnalisés via ReportLab
│   └── search_service.py → Agent de recherche web automatisé via DuckDuckGo
│
├── .cache_audits/        → (Généré automatiquement) Cache local JSON pour éviter les appels LLM redondants
├── .env                  → Variables d'environnement (clés d'API)
├── .gitignore            → Exclusion des clés d'API, du venv et du cache
├── main.py               → Point d'entrée de l'API FastAPI, routes REST et middleware CORS
└── requirements.txt      → Liste des dépendances Python du projet

```

---

## Fonctionnalités Clés

1. **Multi-Provider LLM & Modèles Légers** : Basculement à la volée entre **Gemini** (Cloud) et **Ollama** (Local). Optimisé pour tourner sur des machines modestes grâce à la génération sectionnée pour `qwen2.5:1.5b` ou `phi3:mini`.
2. **Génération Adaptée à l'Objectif** : Ajustement des consignes d'analyse selon l'usage souhaité (`entretien`, `candidature`, `collaboration`, `etude_marche`, `general`).
3. **Système de Cache Intelligent** : Sauvegarde locale des rapports générés sous `.cache_audits/` pour réduire le temps de réponse et préserver les quotas d'API lors des tests.
4. **Flux PDF Synchrone** : Téléchargement direct du rapport PDF depuis l'API sans stockage temporaire sur le disque serveur.
5. **Auto-Détection des Modèles Locaux** : Endpoint dédié scannant l'instance Ollama active pour remonter la liste des modèles installés sur la machine hôte.

---

## Installation & Configuration

### 1. Prérequis

* Python 3.10+
* Ollama installé sur la machine ([https://ollama.com/download](https://ollama.com/download?utm_source=gemini)) pour le support local.

### 2. Cloner et préparer l'environnement

```powershell
# Créer et activer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Sous Windows PowerShell
# source .venv/bin/activate    # Sous Linux/macOS

# Installer les dépendances
pip install -r requirements.txt

```

### 3. Variables d'environnement

Crée un fichier `.env` à la racine du projet :

```env
GEMINI_API_KEY=ta_cle_api_gemini_ici

```

### 4. Télécharger un modèle léger Ollama (Optionnel mais recommandé)

Pour faire tourner le backend 100 % en local sans quota :

```powershell
ollama pull qwen2.5:1.5b
# ou
ollama pull phi3:mini

```

---

## Lancer le Projet

Exécute le serveur Uvicorn avec rechargement automatique :

```powershell
uvicorn main:app --reload

```

* **API de base** : `[http://127.0.0.1:8000](http://127.0.0.1:8000)`
* **Documentation interactive Swagger UI** : `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`

---

## Endpoints API

| Méthode | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Vérification de l'état de l'API. |
| `GET` | `/api/models` | Liste les modèles disponibles (Ollama locaux et Gemini cloud). |
| `POST` | `/api/audit` | Génère et renvoie la fiche d'audit structurée au format JSON. |
| `POST` | `/api/audit/pdf` | Génère et renvoie le rapport sous forme de fichier PDF téléchargeable. |

### Exemple de corps de requête (`POST /api/audit` ou `/api/audit/pdf`) :

```json
{
  "company_name": "Doctolib",
  "provider": "ollama",
  "model_name": "qwen2.5:1.5b",
  "objectif": "entretien"
}

```

---

## Notes Importantes

* **Sécurité & Git** : Le fichier `.env` et le dossier `.cache_audits/` sont strictement ignorés par Git via `.gitignore`. Ne commite jamais tes clés d'API publiques.
* **Inférence Locale** : Lors de l'utilisation du provider `ollama`, l'application Ollama doit être en cours d'exécution en arrière-plan sur la machine hôte.
* **Déploiement** : Ce backend est prêt pour être déployé sur un VPS, Render, Koyeb ou Docker (nécessite une variable d'environnement `GEMINI_API_KEY`).

---

## Pistes d'Évolution

* Intégration d'un système de scraping approfondi avec Puppeteer/Playwright pour contourner le blocage de certains sites d'actualités.
* Ajout d'une base de données PostgreSQL / MongoDB pour conserver l'historique complet des audits des utilisateurs.
* Mise en place d'une file d'attente de tâches de fond (Celery / Redis) pour la génération de rapports volumineux en asynchrone.