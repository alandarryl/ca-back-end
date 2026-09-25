import os
import re
import json
import hashlib
from pathlib import Path
from typing import Literal, Optional

from google import genai
import ollama
from dotenv import load_dotenv
from schemas.audit_schema import CompanyAuditSchema

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

ObjectiveType = Literal["candidature", "entretien", "collaboration", "etude_marche", "general"]

CACHE_DIR = Path(".cache_audits")
CACHE_DIR.mkdir(exist_ok=True)

# Instructions spécifiques selon l'usage final du rapport.
# C'est ça qui change vraiment la pertinence du contenu généré.
OBJECTIVE_INSTRUCTIONS: dict[str, str] = {
    "candidature": (
        "L'utilisateur prépare une CANDIDATURE. Mets l'accent sur : la culture d'entreprise, "
        "les valeurs affichées, le processus de recrutement connu, les compétences/technologies "
        "recherchées, les avis d'anciens employés, et des arguments concrets à réutiliser dans "
        "une lettre de motivation."
    ),
    "entretien": (
        "L'utilisateur prépare un ENTRETIEN D'EMBAUCHE. Mets l'accent sur : les questions "
        "probables côté recruteur, les sujets d'actualité de l'entreprise à mentionner, les "
        "points forts/faibles à connaître pour ne pas être pris au dépourvu, et des questions "
        "pertinentes à poser en fin d'entretien."
    ),
    "collaboration": (
        "L'utilisateur évalue une COLLABORATION B2B (partenariat, prestation, fournisseur). "
        "Mets l'accent sur : la solidité financière, la réputation professionnelle, les "
        "partenariats existants, les risques (litiges, procédures collectives, avis clients "
        "négatifs), et la fiabilité perçue de l'entreprise."
    ),
    "etude_marche": (
        "L'utilisateur réalise une ÉTUDE DE MARCHÉ. Mets l'accent sur : le positionnement "
        "concurrentiel, la taille de marché adressée, la stratégie produit, les tendances du "
        "secteur, et une analyse SWOT étayée par des faits vérifiables."
    ),
    "general": (
        "Fournis une vision globale et équilibrée de l'entreprise, utile dans plusieurs "
        "contextes (candidature, partenariat, veille)."
    ),
}

# Sections utilisées pour la génération "détaillée" (multi-appels, utile pour Ollama).
SECTIONS: list[tuple[str, str]] = [
    ("identite", "Identité : date de création, siège social, effectif, forme juridique, "
                  "dirigeants clés, actionnariat."),
    ("activite", "Activité : produits/services précis, marchés cibles, proposition de valeur, "
                  "clients types."),
    ("finances", "Finances : chiffre d'affaires (avec ordre de grandeur et année), résultats, "
                  "levées de fonds, principaux investisseurs, rentabilité connue."),
    ("marche", "Marché & concurrence : 3 à 5 concurrents nommés, positionnement, avantages "
                "compétitifs, tendances sectorielles actuelles."),
    ("culture", "Culture d'entreprise : valeurs, ambiance de travail rapportée, politique RH, "
                 "note Glassdoor/indeed si connue, avantages salariés."),
    ("actualites", "Actualités des 12-18 derniers mois : annonces, partenariats, recrutements "
                    "massifs, difficultés, changements de direction."),
    ("swot", "Analyse SWOT détaillée : forces, faiblesses, opportunités, menaces, chacune "
              "justifiée par un fait concret."),
    ("conseils", "Conseils pratiques adaptés à l'objectif de l'utilisateur (voir consigne "
                  "d'objectif) : angles à exploiter, pièges à éviter, questions à préparer."),
]

MIN_WORDS_PER_SECTION = 120


# ============================================================
# PROMPT BUILDING
# ============================================================

def _schema_json() -> str:
    return json.dumps(CompanyAuditSchema.model_json_schema(), indent=2, ensure_ascii=False)


def build_full_prompt(company_name: str, raw_data: str, objectif: ObjectiveType) -> str:
    """Prompt unique et détaillé, utilisé pour Gemini (contexte large, pas de souci de longueur)."""
    objectif_txt = OBJECTIVE_INSTRUCTIONS.get(objectif, OBJECTIVE_INSTRUCTIONS["general"])

    return f"""
Tu es un analyste senior spécialisé en intelligence économique et en préparation
professionnelle (recrutement, partenariats, études de marché).

OBJECTIF DE CE RAPPORT :
{objectif_txt}

CONSIGNES DE RÉDACTION (IMPORTANT) :
- Sois EXHAUSTIF et CONCRET : chaque section doit contenir des faits précis
  (dates, chiffres, noms propres), pas des généralités du type "l'entreprise est innovante".
- Vise au moins {MIN_WORDS_PER_SECTION} mots par section textuelle du schéma.
- Si une information n'est pas disponible dans les données fournies, indique
  explicitement "information non trouvée" plutôt que d'inventer.
- Cite les tendances/chiffres avec leur période/année quand c'est possible.
- Structure les listes (concurrents, forces/faiblesses, conseils) avec plusieurs
  éléments distincts, pas un seul item générique.

Analyse l'entreprise "{company_name}" à partir des données ci-dessous et génère
une fiche d'audit COMPLÈTE.

RÉPONDS UNIQUEMENT AVEC UN OBJET JSON RESPECTANT STRICTEMENT CE SCHÉMA (aucun texte
avant/après, pas de balises markdown) :
{_schema_json()}

DONNÉES BRUTES COLLECTÉES :
{raw_data}
""".strip()


def build_section_prompt(company_name: str, raw_data: str, objectif: ObjectiveType,
                          section_key: str, section_desc: str) -> str:
    """Prompt ciblé sur UNE section, pour les petits modèles locaux (Ollama)."""
    objectif_txt = OBJECTIVE_INSTRUCTIONS.get(objectif, OBJECTIVE_INSTRUCTIONS["general"])

    return f"""
Tu es un analyste qui rédige UNE SEULE section d'un rapport d'entreprise détaillé.

Contexte d'usage du rapport : {objectif_txt}

Entreprise analysée : "{company_name}"
Section à rédiger : {section_key} — {section_desc}

Consignes :
- Rédige au moins {MIN_WORDS_PER_SECTION} mots, uniquement sur cette section.
- Utilise des faits concrets (dates, chiffres, noms) tirés des données ci-dessous.
- Si l'info manque, écris "information non trouvée" plutôt que d'inventer.
- Réponds UNIQUEMENT avec un objet JSON de la forme {{"{section_key}": "..."}}
  (ou une liste si la section attend une liste), sans texte autour.

Données brutes :
{raw_data}
""".strip()


# ============================================================
# JSON EXTRACTION / REPAIR
# ============================================================

def _extract_json(raw_output: str) -> str:
    match = re.search(r"\{.*\}", raw_output.strip(), re.DOTALL)
    return match.group(0) if match else raw_output


def _try_parse(raw_output: str) -> Optional[dict]:
    try:
        return json.loads(_extract_json(raw_output))
    except (json.JSONDecodeError, ValueError):
        return None


# ============================================================
# CACHE (évite de repayer les mêmes appels en dev/tests)
# ============================================================

def _cache_key(company_name: str, provider: str, model_name: str, objectif: str) -> Path:
    raw_key = f"{company_name}|{provider}|{model_name}|{objectif}"
    h = hashlib.sha256(raw_key.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


def _cache_get(key: Path) -> Optional[dict]:
    if key.exists():
        return json.loads(key.read_text(encoding="utf-8"))
    return None


def _cache_set(key: Path, data: dict) -> None:
    key.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# PROVIDERS (signatures conservées, param `objectif` ajouté en option)
# ============================================================

def generate_with_gemini(company_name: str, raw_data: str, model_name: str,
                          objectif: ObjectiveType = "general") -> str:
    """Génération via l'API Gemini (inchangé dans son fonctionnement, prompt enrichi)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé GEMINI_API_KEY manquante dans le .env")

    client = genai.Client(api_key=api_key)
    prompt = build_full_prompt(company_name, raw_data, objectif)

    response = client.interactions.create(
        model=model_name,
        input=prompt
    )
    return response.output_text


def generate_with_ollama(company_name: str, raw_data: str, model_name: str,
                          objectif: ObjectiveType = "general") -> str:
    """Génération en un seul appel (comportement d'origine, prompt enrichi)."""
    system_prompt = "Tu es un assistant JSON strict. Tu réponds UNIQUEMENT avec un objet JSON valide et rien d'autre."
    user_prompt = build_full_prompt(company_name, raw_data, objectif)

    response = ollama.chat(
        model=model_name,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        format="json"
    )
    return response['message']['content']


def generate_with_ollama_sectioned(company_name: str, raw_data: str, model_name: str,
                                    objectif: ObjectiveType = "general") -> dict:
    """
    Génère le rapport SECTION PAR SECTION avec Ollama.
    Beaucoup plus fiable qu'un seul gros appel pour les petits modèles
    (qwen2.5:1.5b, etc.) qui tronquent souvent les longs JSON.
    """
    merged: dict = {}
    system_prompt = "Tu es un assistant JSON strict. Tu réponds UNIQUEMENT avec un objet JSON valide et rien d'autre."

    for section_key, section_desc in SECTIONS:
        prompt = build_section_prompt(company_name, raw_data, objectif, section_key, section_desc)
        response = ollama.chat(
            model=model_name,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            format="json"
        )
        parsed = _try_parse(response['message']['content'])
        if parsed:
            merged.update(parsed)
        else:
            merged[section_key] = "information non trouvée"

    return merged


# ============================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================

def generate_company_audit(
    company_name: str,
    raw_data: str,
    provider: str = "ollama",
    model_name: str = "qwen2.5:1.5b",
    objectif: ObjectiveType = "general",
    detailed: bool = True,
    use_cache: bool = True,
) -> CompanyAuditSchema:
    """
    provider : "ollama" ou "gemini"
    objectif : adapte le contenu du rapport à l'usage réel (candidature, entretien, ...)
    detailed : si True et provider="ollama", utilise la génération sectionnée
               (plus lente mais beaucoup plus complète pour les petits modèles).
    """
    cache_key = _cache_key(company_name, provider, model_name, objectif)
    if use_cache:
        cached = _cache_get(cache_key)
        if cached:
            return CompanyAuditSchema.model_validate(cached)

    if provider == "ollama":
        if detailed:
            data = generate_with_ollama_sectioned(company_name, raw_data, model_name, objectif)
        else:
            raw_output = generate_with_ollama(company_name, raw_data, model_name, objectif)
            data = _try_parse(raw_output) or {}
    else:
        raw_output = generate_with_gemini(company_name, raw_data, model_name, objectif)
        data = _try_parse(raw_output) or {}

    audit = CompanyAuditSchema.model_validate(data)

    if use_cache:
        _cache_set(cache_key, audit.model_dump())

    return audit


if __name__ == "__main__":
    from services.search_service import search_company_info

    print("Recherche des infos...")
    raw_info = search_company_info("Doctolib")

    print("Génération détaillée (sectionnée) avec Qwen2.5, objectif = entretien...")
    audit = generate_company_audit(
        "Doctolib",
        raw_info,
        provider="ollama",
        model_name="qwen2.5:1.5b",
        objectif="entretien",
        detailed=True,
    )

    print("\n--- RÉSULTAT ---")
    print(audit.model_dump_json(indent=2))