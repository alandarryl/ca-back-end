import os
import re
import json
from google import genai
from dotenv import load_dotenv
from schemas.audit_schema import CompanyAuditSchema

load_dotenv()

def generate_company_audit(company_name: str, raw_data: str) -> CompanyAuditSchema:
    """
    Analyse les données brutes collectées et génère une fiche d'audit structurée.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La clé GEMINI_API_KEY n'est pas définie dans le fichier .env")

    client = genai.Client(api_key=api_key)

    # Récupération de la structure exacte attendue par Pydantic
    schema_definition = CompanyAuditSchema.model_json_schema()

    prompt = f"""
    Tu es un expert en préparation d'entretiens d'embauche.
    Analyse les informations suivantes concernant l'entreprise '{company_name}' et génère une fiche d'audit synthétique.

    TU DOIS IMPÉRATIVEMENT RÉPONDRE UNIQUEMENT AVEC UN OBJET JSON VALIDE qui respecte ce schéma :
    {json.dumps(schema_definition, indent=2, ensure_ascii=False)}

    Exemple de structure attendue :
    {{
        "company_name": "{company_name}",
        "summary": "Résumé de deux phrases...",
        "products_and_services": ["Service 1", "Service 2"],
        "company_culture": ["Valeur 1", "Valeur 2"],
        "interview_questions": ["Question 1", "Question 2"],
        "recent_news": ["Actualité 1", "Actualité 2"]
    }}

    Données brutes :
    {raw_data}
    """

    response = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt
    )

    raw_output = response.output_text.strip()

    # Nettoyage si Gemini entoure sa réponse de balises Markdown ```json ... ```
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if match:
        clean_json = match.group(0)
    else:
        clean_json = raw_output

    return CompanyAuditSchema.model_validate_json(clean_json)


if __name__ == "__main__":
    from services.search_service import search_company_info
    
    print("Recherche des infos...")
    raw_info = search_company_info("Doctolib")
    
    print("Génération de l'audit via Gemini...")
    audit = generate_company_audit("Doctolib", raw_info)
    
    print("\n--- RÉSULTAT OBTENU ---")
    print(audit.model_dump_json(indent=2))