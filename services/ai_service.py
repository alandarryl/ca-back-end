import os
import re
import json
from google import genai
import ollama
from dotenv import load_dotenv
from schemas.audit_schema import CompanyAuditSchema

load_dotenv()

def generate_with_gemini(company_name: str, raw_data: str, model_name: str) -> str:
    """Génération via l'API Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé GEMINI_API_KEY manquante dans le .env")

    client = genai.Client(api_key=api_key)
    schema_def = CompanyAuditSchema.model_json_schema()

    prompt = f"""
    Tu es un expert en préparation d'entretiens.
    Analyse l'entreprise '{company_name}' et génère une fiche d'audit synthétique.
    
    RÉPONDS UNIQUEMENT AVEC UN OBJET JSON RESPECTANT CE SCHÉMA :
    {json.dumps(schema_def, indent=2, ensure_ascii=False)}

    Données :
    {raw_data}
    """

    response = client.interactions.create(
        model=model_name,
        input=prompt
    )
    return response.output_text


def generate_with_ollama(company_name: str, raw_data: str, model_name: str) -> str:
    """Génération en local via Ollama (optimisé pour modèles légers)."""
    schema_def = CompanyAuditSchema.model_json_schema()

    # System prompt plus direct pour guider les petits modèles
    system_prompt = "Tu es un assistant JSON strict. Tu réponds UNIQUEMENT avec un objet JSON valide et rien d'autre."
    
    user_prompt = f"""
    Analyse l'entreprise '{company_name}' à partir des données ci-dessous et complète le schéma JSON.

    Schéma à respecter :
    {json.dumps(schema_def, indent=2, ensure_ascii=False)}

    Données brutes :
    {raw_data}
    """

    response = ollama.chat(
        model=model_name,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        format="json"  # Force le mode JSON natif d'Ollama
    )
    return response['message']['content']


def generate_company_audit(
    company_name: str, 
    raw_data: str, 
    provider: str = "ollama", 
    model_name: str = "qwen2.5:1.5b"
) -> CompanyAuditSchema:
    
    if provider == "ollama":
        raw_output = generate_with_ollama(company_name, raw_data, model_name)
    else:
        raw_output = generate_with_gemini(company_name, raw_data, model_name)

    # Extraction sécurisée par RegEx
    match = re.search(r"\{.*\}", raw_output.strip(), re.DOTALL)
    clean_json = match.group(0) if match else raw_output

    return CompanyAuditSchema.model_validate_json(clean_json)


if __name__ == "__main__":
    from services.search_service import search_company_info
    
    print("Recherche des infos...")
    raw_info = search_company_info("Doctolib")
    
    print("Génération locale avec Qwen2.5...")
    audit = generate_company_audit("Doctolib", raw_info, provider="ollama", model_name="qwen2.5:1.5b")
    
    print("\n--- RÉSULTAT LOCAL ---")
    print(audit.model_dump_json(indent=2))