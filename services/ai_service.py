import os
from google import genai
from google.genai import types
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

    prompt = f"""
    Tu es un expert en préparation d'entretiens d'embauche.
    Analyse les informations suivantes concernant l'entreprise '{company_name}' et génère une fiche d'audit synthétique.

    Données brutes :
    {raw_data}
    """

    # Forcer Gemini à répondre strictement au format JSON défini par notre schéma Pydantic
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CompanyAuditSchema,
            temperature=0.2,
        ),
    )

    # Convertir la réponse JSON brute en objet Pydantic
    return CompanyAuditSchema.model_validate_json(response.text)


# test
if __name__ == "__main__":
    from services.search_service import search_company_info

    print("Recherche des infos...")
    raw_info = search_company_info("Doctolib")

    print("Génération de l'audit via Gemini...")
    audit = generate_company_audit("Doctolib", raw_info)

    print("\n--- RÉSULTAT OBTENU ---")
    print(audit.model_dump_json(indent=2))